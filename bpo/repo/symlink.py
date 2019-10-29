# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import os.path
import shutil

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
    os.makedirs(path, exist_ok=True)


def find_apk(wip, final, package):
    """ :param wip: path to WIP repository
        :param final: path to final repository
        :param package: bpo.db.Package object """
    apk = package.pkgname + "-" + package.version + ".apk"
    apk_wip = wip + "/" + apk
    if os.path.exists(apk_wip):
        return apk_wip

    apk_final = final + "/" + apk
    if os.path.exists(apk_final):
        return apk_final

    raise RuntimeError("Found package in database, but not in WIP or final"
                       " repository: " + apk)


def link_to_all_packages(arch, branch, force=False):
    """ Create symlinks to new packages from WIP repo and to up-to-date
        packages from final repo. """

    repo_symlink = get_path(arch, branch)
    repo_wip = bpo.repo.wip.get_path(arch, branch)
    repo_final = bpo.repo.final.get_path(arch, branch)
    session = bpo.db.session()
    packages = session.query(bpo.db.Package).filter_by(arch=arch,
                                                       branch=branch)

    # Sanity check: make sure that all packages exist in wip or final repo
    if not force:
        for package in packages:
            find_apk(repo_wip, repo_final, package)

    # Remove outdated packages in WIP repo
    bpo.repo.wip.clean(arch, branch)

    # Link to everything in WIP repo
    os.makedirs(repo_symlink, exist_ok=True)
    for apk in bpo.repo.get_apks(arch, branch, repo_wip):
        apk_wip = os.path.realpath(repo_wip + "/" + apk)
        os.symlink(apk_wip, repo_symlink + "/" + apk)

    # Link to relevant packages from final repo
    for apk in bpo.repo.get_apks(arch, branch, repo_final):
        apk_final = os.path.realpath(repo_final + "/" + apk)
        if bpo.repo.is_apk_origin_in_db(session, arch, branch, apk_final):
            os.symlink(apk_final, repo_symlink + "/" + apk)


def sign(arch, branch):
    # Copy index to wip repo (just because that makes it easy to download it)
    repo_wip_path = bpo.repo.wip.get_path(arch, branch)
    src = get_path(arch, branch) + "/APKINDEX.tar.gz"
    dst = repo_wip_path + "/APKINDEX-symlink-repo.tar.gz"
    os.makedirs(repo_wip_path, exist_ok=True)
    shutil.copy(src, dst)

    # Sign it with a job
    bpo.jobs.sign_index.run(arch, branch)


def create(arch, branch, force=False):
    # Skip if WIP repo is empty
    repo_wip_path = bpo.repo.wip.get_path(arch, branch)
    if not force and not len(bpo.repo.get_apks(arch, branch, repo_wip_path)):
        logging.debug("{}@{}: empty WIP repo, skipping creation of symlink"
                      " repo".format(arch, branch))
        return

    logging.info("{}@{}: creating symlink repo".format(arch, branch))
    clean(arch, branch)
    link_to_all_packages(arch, branch, force)
    bpo.repo.tools.index(arch, branch, "symlink", get_path(arch, branch))
    sign(arch, branch)
