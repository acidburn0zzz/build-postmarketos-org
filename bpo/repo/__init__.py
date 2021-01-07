# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os

import bpo.config.const
import bpo.db
import bpo.helpers.apk
import bpo.jobs.build_image
import bpo.jobs.build_package
import bpo.jobs.sign_index
import bpo.repo.symlink
import bpo.repo.tools
import bpo.repo.wip


def next_package_to_build(session, arch, branch):
    """ :returns: pkgname """

    # Get all packages for arch where status = failed and retries left
    failed = bpo.db.PackageStatus.failed
    retry_count_max = bpo.config.const.retry_count_max
    result = session.query(bpo.db.Package)\
                    .filter_by(arch=arch, branch=branch, status=failed)\
                    .filter(bpo.db.Package.retry_count < retry_count_max)\
                    .all()

    # Get all packages for arch where status = queued
    queued = bpo.db.PackageStatus.queued
    result += session.query(bpo.db.Package)\
                     .filter_by(arch=arch, branch=branch, status=queued)\
                     .all()

    if not len(result):
        return None

    for package in result:
        if package.depends_built():
            return package.pkgname

    # Can't resolve (this is expected, if we only have packages left that
    # depend on packages that are currently building.)
    logging.debug("can't resolve remaining packages: " + str(result))
    return None


def next_image_to_build(session, branch):
    """ :returns: image db object """
    # Check images where status = failed and retries left
    failed = bpo.db.ImageStatus.failed
    retry_count_max = bpo.config.const.retry_count_max
    result = session.query(bpo.db.Image)\
        .filter_by(branch=branch, status=failed)\
        .filter(bpo.db.Image.retry_count < retry_count_max)\
        .all()
    if len(result):
        return result[0]

    # Check images in queue
    queued = bpo.db.ImageStatus.queued
    result = session.query(bpo.db.Image)\
        .filter_by(branch=branch, status=queued)\
        .all()
    return result[0] if len(result) else None


def count_running_builds_packages(session):
    building = bpo.db.PackageStatus.building
    return session.query(bpo.db.Package).filter_by(status=building).count()


def count_running_builds_images(session):
    building = bpo.db.ImageStatus.building
    return session.query(bpo.db.Image).filter_by(status=building).count()


def count_running_builds(session):
    return (count_running_builds_packages(session) +
            count_running_builds_images(session))


def count_unpublished_packages(session, branch):
    return session.query(bpo.db.Package).\
            filter_by(branch=branch).\
            filter(bpo.db.Package.status != bpo.db.PackageStatus.published).\
            count()


def has_unfinished_builds(session, arch, branch):
    for status in bpo.db.PackageStatus.failed, bpo.db.PackageStatus.building:
        if session.query(bpo.db.Package).filter_by(status=status, arch=arch,
                                                   branch=branch).count():
            return True
    return False


def set_stuck(arch, branch):
    """ No more packages can be built, because all remaining packages in the
        queue have already failed, or depend on packages that have failed. This
        is an extra function, so we can hook it in the tests. """
    logging.info(branch + "/" + arch + ": repo is stuck")


def build_arch_branch(session, slots_available, arch, branch,
                      force_repo_update=False):
    """ :returns: amount of jobs that were started
        :param force_repo_update: rebuild the symlink and final repo, even if
                                  no new packages were built. Set this to True
                                  after deleting packages in the database, so
                                  the apks get removed from the final repo. """
    logging.info(branch + "/" + arch + ": starting new package build job(s)")
    started = 0
    while True:
        pkgname = next_package_to_build(session, arch, branch)
        if not pkgname:
            if not started:
                if has_unfinished_builds(session, arch, branch):
                    set_stuck(arch, branch)
                else:
                    logging.info(branch + "/" + arch + ": WIP repo complete")
                    bpo.repo.symlink.create(arch, branch, force_repo_update)
            break

        if slots_available > 0:
            if bpo.jobs.build_package.run(arch, pkgname, branch):
                started += 1
                slots_available -= 1
        else:
            break
    return started


def build_images_branch(session, slots_available, branch):
    """ :returns: amount of jobs that were started """
    logging.info(f"{branch}: starting new image build jobs")
    started = 0

    while slots_available:
        image = next_image_to_build(session, branch)
        if not image:
            break

        bpo.jobs.build_image.run(image.device, image.branch, image.ui)
        started += 1
        slots_available -= 1

    return started


def build(force_repo_update=False):
    """ Start as many parallel build jobs, as configured. When all packages are
        built, publish the packages. (Images get published right after they
        get submitted to the server in bpo/api/job_callback/build_image.py, not
        here.)
        :param force_repo_update: rebuild the symlink and final repo, even if
                                  no new packages were built. Set this to True
                                  after deleting packages in the database, so
                                  the apks get removed from the final repo. """
    session = bpo.db.session()
    running = count_running_builds(session)
    slots_available = bpo.config.const.max_parallel_build_jobs - running

    # Iterate over all branch-arch combinations, to give them a chance to start
    # a new job or to proceed with rolling out their fully built WIP repo
    for branch, branch_data in bpo.config.const.branches.items():
        for arch in branch_data["arches"]:
            slots_available -= build_arch_branch(session, slots_available,
                                                 arch, branch,
                                                 force_repo_update)
    if slots_available <= 0:
        return

    # Iterate over branches and build images
    for branch in bpo.config.const.branches:
        # Only build images on branches where all packages are published
        if count_unpublished_packages(session, branch):
            continue

        slots_available -= build_images_branch(session, slots_available,
                                               branch)
        if slots_available <= 0:
            break


def get_apks(cwd):
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
