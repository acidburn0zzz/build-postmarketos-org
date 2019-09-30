# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import shutil
import subprocess

import bpo.config.const


def get_path(arch, branch):
    return "{}/{}/{}".format(bpo.config.args.repo_final_path, branch, arch)


def copy_new_apks(arch, branch):
    logging.info(branch + "@" + arch + ": copying new apks from symlink to"
                 " final repo")
    repo_final_path = get_path(arch, branch)
    repo_symlink_path = bpo.repo.symlink.get_path(arch, branch)

    subprocess.run(["mkdir", "-p", repo_final_path], check=True)

    for apk in bpo.repo.get_apks(arch, branch, repo_symlink_path):
        src = os.path.realpath(repo_symlink_path + "/" + apk)
        dst = os.path.realpath(repo_final_path + "/" + apk)
        if src == dst:
            logging.debug(apk + ": symlink points to final repo, not copying")
            continue
        logging.debug(apk + ": copying to final repo")
        shutil.copy(src, dst)


def copy_new_apkindex(arch, branch):
    logging.info(branch + "@" + arch + ": copying new APKINDEX")
    src = bpo.repo.symlink.get_path(arch, branch) + "/APKINDEX.tar.gz"
    dst = get_path(arch, branch) + "/APKINDEX.tar.gz"
    shutil.copy(src, dst)


def delete_outdated_apks(arch, branch):
    logging.info(branch + "@" + arch + ": removing outdated apks")
    repo_final_path = get_path(arch, branch)
    repo_symlink_path = bpo.repo.symlink.get_path(arch, branch)

    for apk in bpo.repo.get_apks(arch, branch, repo_final_path):
        if os.path.exists(repo_symlink_path + "/" + apk):
            continue
        logging.info(apk + ": does not exist in symlink repo, removing")
        os.unlink(repo_final_path + "/" + apk)


def update_from_symlink_repo(arch, branch):
    copy_new_apks(arch, branch)
    copy_new_apkindex(arch, branch)
    delete_outdated_apks(arch, branch)


def publish(arch, branch):
    logging.info("STUB: bpo.repo.final.publish")
