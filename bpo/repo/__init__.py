# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

import bpo.config.const
import bpo.db
import bpo.jobs.build_package
import bpo.jobs.sign_index


def publish(arch, branch):
    logging.info("STUB: bpo.helpers.repo.publish")

    # TODO:
    # * run rsync to publish the repo
    # * better do it in a retry-loop, in case it fails
    # * update database


def index(arch, branch):
    logging.info("STUB: bpo.helpers.repo.index")

    # TODO:
    # * rebuild APKINDEX locally
    # * update database
    # bpo.jobs.sign_index.run(arch)


def next_package_to_build(session, arch, branch):
    """ :returns: pkgname """

    # Get all packages for arch where status = waiting
    waiting = bpo.db.PackageStatus.waiting
    result = session.query(bpo.db.Package).filter_by(arch=arch,
                                                     branch=branch,
                                                     status=waiting).all()
    if not len(result):
        return None

    for package in result:
        if package.depends_built():
            return package.pkgname
    raise RuntimeError("can't resolve remaining packages: " + result.join(","))


def count_running_builds(session):
    building = bpo.db.PackageStatus.building
    result = session.query(bpo.db.Package).filter_by(status=building).all()
    return len(result)


def build(arch, branch):
    """ Start as many parallel build package jobs, as configured. When all
        packages are built, publish the packages. """
    session = bpo.db.session()
    running = count_running_builds(session)

    if running >= bpo.config.const.max_parallel_build_jobs:
        logging.info("Building " + arch + "@" + branch + ": max parallel build"
                     " jobs already running, starting more jobs is delayed.")
        # FIXME: add logic to retry building for all arches+branches when a
        # package was built. maybe rewrite this function to always take all
        # branches and arches into account?
        return

    logging.info("Building " + arch + "@" + branch + ": starting new job(s)")
    while running < bpo.config.const.max_parallel_build_jobs:
        pkgname = next_package_to_build(session, arch, branch)
        if not pkgname:
            break

        bpo.jobs.build_package.run(arch, pkgname, branch)
        running += 1

    if not running:
        index(arch, branch)
    return
