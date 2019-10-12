# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import subprocess

import bpo.config.const
import bpo.repo
import bpo.repo.final


def get_path(arch, branch):
    return "{}/{}/{}".format(bpo.config.args.repo_wip_path, branch, arch)


def do_keygen():
    """ Generate key for signing the APKINDEX of the WIP repository locally."""

    # Skip if pub key exists
    path_dir = bpo.config.const.repo_wip_keys
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


def update_apkindex(arch, branch):
    path = get_path(arch, branch)
    if os.path.exists(path):
        bpo.repo.tools.index(arch, branch, "WIP", path)
        sign(arch, branch)


def clean(arch, branch):
    """ Delete all apks from WIP repo, that are either in final repo or not in
        the db anymore (pmaport updated or deleted), and update the APKINDEX
        of the WIP repo. """
    logging.debug("Cleaning WIP repo")
    path_repo_wip = get_path(arch, branch)
    path_repo_final = bpo.repo.final.get_path(arch, branch)
    session = bpo.db.session()

    for apk in bpo.repo.get_apks(arch, branch, path_repo_wip):
        apk_wip = path_repo_wip + "/" + apk
        # Find in final repo
        if os.path.exists(path_repo_final + "/" + apk):
            logging.debug(apk + ": found in final repo, delete from WIP repo")
            os.unlink(apk_wip)
            continue

        # Find in db
        if bpo.repo.is_apk_origin_in_db(session, arch, branch, apk_wip):
            logging.debug(apk + ": not in final repo, but found in db ->"
                          " keeping in WIP repo")
        else:
            logging.debug(apk + ": not found in db, delete from WIP repo")
            os.unlink(apk_wip)

    update_apkindex(arch, branch)
