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


def extract():
    temp_path_prepare()
    extract_tool_apk("apk-tools-static", ["sbin/apk.static"])
    extract_tool_apk("abuild-sign-noinclude", ["usr/bin/abuild-sign.noinclude",
                                               "usr/bin/abuild-tar.static"])

def index_staging(arch, branch):
    logging.info("STUB: bpo.repo.tools.index_staging")


def sign_staging(arch, branch):
    logging.info("STUB: bpo.repo.tools.sign_staging")
