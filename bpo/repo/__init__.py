# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os

import bpo.config.const
import bpo.db
import bpo.helpers.apk
import bpo.jobs.build_package
import bpo.jobs.sign_index
import bpo.repo.symlink
import bpo.repo.tools
import bpo.repo.wip


def next_package_to_build(session, arch, branch):
    """ :returns: pkgname """

    # Get all packages for arch where status = queued
    queued = bpo.db.PackageStatus.queued
    result = session.query(bpo.db.Package).filter_by(arch=arch,
                                                     branch=branch,
                                                     status=queued).all()
    if not len(result):
        return None

    for package in result:
        if package.depends_built():
            return package.pkgname

    # Can't resolve (this is expected, if we only have packages left that
    # depend on packages that are currently building.)
    logging.debug("can't resolve remaining packages: " + str(result))
    return None


def count_running_builds(session):
    building = bpo.db.PackageStatus.building
    return session.query(bpo.db.Package).filter_by(status=building).count()


def count_failed_builds(session, arch, branch):
    failed = bpo.db.PackageStatus.failed
    return session.query(bpo.db.Package).filter_by(status=failed, arch=arch,
                                                   branch=branch).count()


def build_arch_branch(session, slots_available, arch, branch):
    """ :returns: amount of jobs that were started """
    logging.info("Building " + arch + "@" + branch + ": starting new job(s)")
    running = 0
    while True:
        pkgname = next_package_to_build(session, arch, branch)
        if not pkgname:
            if not running:
                if count_failed_builds(session, arch, branch):
                    bpo.ui.log("build_repo_stuck", arch=arch, branch=branch)
                else:
                    logging.info(arch + "@" + branch + ": WIP repo complete")
                    bpo.repo.symlink.create(arch, branch)
            break

        if slots_available > 0:
            if bpo.jobs.build_package.run(arch, pkgname, branch):
                running += 1
                slots_available -= 1
        else:
            break
    return running


def build():
    """ Start as many parallel build package jobs, as configured. When all
        packages are built, publish the packages. """
    session = bpo.db.session()
    running = count_running_builds(session)
    slots_available = bpo.config.const.max_parallel_build_jobs - running

    # Iterate over all branch-arch combinations, to give them a chance to start
    # a new job or to proceed with rolling out their fully built WIP repo
    for branch in bpo.config.const.branches:
        for arch in bpo.config.const.architectures:
            slots_available -= build_arch_branch(session, slots_available,
                                                 arch, branch)


def get_apks(arch, branch, cwd):
    """ Get a sorted list of all apks in a repository.
        :param cwd: path to the repository """
    ret = []
    for apk in glob.glob(cwd + "/*.apk"):
        ret += [os.path.basename(apk)]
    ret.sort()

    return ret


def is_apk_origin_in_db(session, arch, branch, apk_path):
    """ :param apk_path: full path to the apk file
        :returns: True if the origin is in the db and has the same version,
                  False otherwise """

    metadata = bpo.helpers.apk.get_metadata(apk_path)
    pkgname = metadata["origin"]
    version = metadata["pkgver"]  # yes, this is actually the full version
    return bpo.db.package_has_version(session, pkgname, arch, branch, version)
