# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import subprocess

import bpo.config.const


def get_path(arch, branch):
    return "{}/{}/{}".format(bpo.config.args.repo_wip_path, branch, arch)


def do_keygen():
    """ Generate key for signing the APKINDEX of the WIP repository locally."""

    # Skip if pub key exists
    path_dir = bpo.config.const.repo_wip_keys
    path_private = path_dir + "/wip.rsa"
    path_public = path_dir + "/wip.rsa.pub"
    if os.path.exists(path_public):
        return

    # Generate keys (like do_keygen() in abuild-keygen)
    logging.info("Generating RSA keypair for WIP repository")
    os.makedirs(path_dir, exist_ok=True)
    subprocess.run(["openssl", "genrsa", "-out", "wip.rsa", "2048"],
                   check=True, cwd=path_dir)
    subprocess.run(["openssl", "rsa", "-in", "wip.rsa", "-pubout", "-out",
                    "wip.rsa.pub"], check=True, cwd=path_dir)


def sign(arch, branch):
    cmd = ["abuild-sign.noinclude",
           "-k", bpo.config.const.repo_wip_keys + "/wip.rsa",
           "APKINDEX.tar.gz"]
    bpo.repo.tools.run(arch, branch, "WIP", get_path(arch, branch), cmd)


def finish_upload_from_job(arch, branch):
    bpo.repo.tools.index(arch, branch, "WIP", get_path(arch, branch))
    sign(arch, branch)
