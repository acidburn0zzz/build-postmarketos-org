# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import subprocess
import shutil
import tarfile

import bpo.config.const


def temp_path_prepare():
    temp_path = bpo.config.args.temp_path + "/repo_tools"
    if os.path.exists(temp_path):
        subprocess.run(["rm", "-rf", temp_path], check=True)
    subprocess.run(["mkdir", "-p", temp_path + "/bin"], check=True)


def extract_tool_apk(pkgname, paths):
    bin_path = bpo.config.args.temp_path + "/repo_tools/bin"
    pattern = bpo.config.const.top_dir + "/tools/" + pkgname + "-*.apk"
    results = glob.glob(pattern)
    if len(results) != 1:
        raise RuntimeError("There must be exactly one file that matches: " +
                           pattern)

    with tarfile.open(results[0], "r:gz") as tar:
        for path in paths:
            logging.debug("Extracting " + results[0] + ": " + path)
            extract_path = bin_path + "/" + os.path.basename(path)
            with open(extract_path, "w+b") as handle:
                member = tar.getmember(path)
                shutil.copyfileobj(tar.extractfile(member), handle)
                os.chmod(extract_path, 0o755)


def generate_wip_repo_key():
    """ Generate key for signing the APKINDEX of the WIP repository locally."""

    # Skip if pub key exists
    path_dir = bpo.config.const.repo_wip_keys
    path_private = path_dir + "/wip.rsa"
    path_public = path_dir + "/wip.pub"
    if os.path.exists(path_public):
        return

    # Generate keys (like do_keygen() in abuild-keygen)
    logging.info("Generating RSA keypair for WIP repository")
    subprocess.run(["mkdir", "-p", path_dir], check=True)
    subprocess.run(["openssl", "genrsa", "-out", "wip.rsa", "2048"],
                   check=True, cwd=path_dir)
    subprocess.run(["openssl", "rsa", "-in", "wip.rsa", "-pubout", "-out",
                    "wip.pub"], check=True, cwd=path_dir)


def init():
    temp_path_prepare()
    extract_tool_apk("apk-tools-static", ["sbin/apk.static"])
    extract_tool_apk("abuild-sign-noinclude", ["usr/bin/abuild-sign.noinclude",
                                               "usr/bin/abuild-tar.static"])
    generate_wip_repo_key()


def run_in_wip_repo(arch, branch, cmd):
    cwd = bpo.config.args.repo_wip_path + "/" + branch + "/" + arch
    tools_bin = bpo.config.args.temp_path + "/repo_tools/bin"
    env = {"PATH": tools_bin + ":" + os.getenv("PATH") }

    logging.debug("{}@{}: running in WIP repo: {}".format(arch, branch, cmd))
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def get_wip_repo_apks(arch, branch):
    pattern = "{}/{}/{}/*.apk".format(bpo.config.args.repo_wip_path, branch,
                                      arch)
    apks = glob.glob(pattern)
    ret = []
    for apk in apks:
        ret += [os.path.basename(apk)]
    ret.sort()

    return ret


def index_wip(arch, branch):
    cmd = ["apk.static", "-q", "index", "--output", "APKINDEX.tar.gz_",
           "--rewrite-arch", arch] + get_wip_repo_apks(arch, branch)
    run_in_wip_repo(arch, branch, cmd)


def sign_wip(arch, branch):
    logging.info("STUB: bpo.repo.tools.sign_wip")
