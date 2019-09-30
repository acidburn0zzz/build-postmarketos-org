# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import shutil
import subprocess

import bpo.config.args
import bpo.db
import bpo.repo.final
import bpo.repo.wip


def get_path(arch, branch):
    # The symlink repo is in the temp path, because it does not take up as much
    # space as the final or wip repos.
    temp_path = bpo.config.args.temp_path
    return "{}/repo_symlink/{}/{}".format(temp_path, branch, arch)


def clean(arch, branch):
    path = get_path(arch, branch)
    if os.path.exists(path):
        shutil.rmtree(path)
    subprocess.run(["mkdir", "-p", path], check=True)


def find_apk(wip, final, package):
    """ :param wip: path to WIP repository
        :param final: path to final repository
        :param package: bpo.db.Package object """
    apk_wip = "{}/{}-{}.apk".format(wip, package.pkgname, package.version)
    if os.path.exists(apk_wip):
        return apk_wip

    apk_final = "{}/{}-{}.apk".format(final, package.pkgname, package.version)
    if os.path.exists(apk_final):
        return apk_final

    raise RuntimeError("Found package in database, but not in WIP or final"
                       " repository: " + Package)


def link_to_all_packages(arch, branch):
    repo_symlink = get_path(arch, branch)
    repo_wip = bpo.repo.wip.get_path(arch, branch)
    repo_final = bpo.repo.final.get_path(arch, branch)
    session = bpo.db.session()
    packages = session.query(bpo.db.Package).filter_by(arch=arch,
                                                       branch=branch)
    for package in packages:
        src = find_apk(repo_wip, repo_final, package)
        logging.debug("new staging repo link: " + src)
        os.symlink(src, repo_symlink + "/" + os.path.basename(src))


def sign(arch, branch):
    # copy index to wip repo (just because that makes it easy to download it)
    # run sign job
    logging.info("STUB: sign symlink repo")


def create(arch, branch):
    # TODO multithreading: make sure that this only runs once at a time
    logging.info("{}@{}: creating symlink repo".format(arch, branch))
    clean(arch, branch)
    link_to_all_packages(arch, branch)
    bpo.repo.tools.index(arch, branch, "symlink", get_path(arch, branch))
    sign(arch, branch)
