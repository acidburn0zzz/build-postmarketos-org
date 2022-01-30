# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import logging

import bpo.db
import bpo.helpers.apk
import bpo.helpers.job
import bpo.repo


def is_apk_broken(metadata):
    if metadata["abuild_version"] == "3.5.0_rc1-r0":  # see #56
        return True
    return False


def remove_broken_apk(session, pkgname, version, arch, branch, apk_path):
    # Remove from disk
    bpo.ui.log("remove_broken_apk", arch=arch, branch=branch, pkgname=pkgname,
               version=version)
    os.unlink(apk_path)

    # Reset package status to queued
    queued = bpo.db.PackageStatus.queued
    package = bpo.db.get_package(session, pkgname, arch, branch)
    if package and package.version == version:
        bpo.db.set_package_status(session, package, queued)
        bpo.ui.log_package(package, "remove_broken_apk_reset_deleted")

    # Reset packages depending on the deleted apk from failed to queued
    failed = bpo.db.PackageStatus.failed
    result = session.query(bpo.db.Package)\
        .filter_by(arch=arch, branch=branch, status=failed)
    for package_failed in result:
        # There's probably a clever way to do this with sqlalchemy filters, but
        # this is not performance critical
        if package not in package_failed.depends:
            continue
        bpo.db.set_package_status(session, package_failed, queued)
        bpo.ui.log_package(package_failed, "remove_broken_apk_reset_failed")


def fix_disk_vs_db(arch, branch, path, status, is_wip=False):
    """ Iterate over apks on disk, fix package status if it is not set to
        built/published but binary packages exist in the wip/final repo. Also
        remove obsolete packages from the wip repo. (Obsolete packages from the
        final repo get removed as the final repo gets updated, it does not make
        sense to delete them beforehand.)
        :param arch: architecture, e.g. "x86_64"
        :param branch: pmaports.git branch, e.g. "master"
        :param path: wip or final repo path, as returned by
                     bpo.repo.{wip,final}.get_path()
        :param status: the package should have when the related apk file exists
                       e.g. bpo.db.PackageStatus.built
        :param is_wip: set to True when looking at the wip repo, False when
                       looking at the final repo. """
    session = bpo.db.session()
    apks = bpo.repo.get_apks(path)
    for apk in apks:
        metadata = bpo.helpers.apk.get_metadata(path + "/" + apk)
        pkgname = metadata["origin"]
        version = metadata["pkgver"]  # metadata pkgver is really full version

        if is_apk_broken(metadata):
            remove_broken_apk(session, pkgname, version, arch, branch,
                              path + "/" + apk)
            continue

        package = bpo.db.get_package(session, pkgname, arch, branch)
        if not package or package.version != version:
            if is_wip:
                os.unlink(path + "/" + apk)
                logging.warning("Removing obsolete wip package: " + apk)
                if package:
                    bpo.ui.log_package(package, "obsolete_wip_package")
                else:
                    bpo.ui.log(action="obsolete_wip_package", arch=arch,
                               branch=branch, pkgname=pkgname, version=version)
            continue
        if package.status != status:
            bpo.db.set_package_status(session, package, status)
            bpo.ui.log_package(package, "package_" + status.name)


def fix_db_vs_disk(arch, branch):
    """ Iterate over packages in db, fix status of packages that are marked as
        built/published but are missing on disk.
        :param arch: architecture, e.g. "x86_64"
        :param branch: pmaports.git branch, e.g. "master" """
    session = bpo.db.session()
    packages = session.query(bpo.db.Package).filter_by(arch=arch,
                                                       branch=branch)
    path_final = bpo.repo.final.get_path(arch, branch)
    path_wip = bpo.repo.wip.get_path(arch, branch)

    for package in packages:
        # Missing published packages: change to "built"
        if (package.status == bpo.db.PackageStatus.published and
            not os.path.exists("{}/{}-{}.apk".format(path_final,
                                                     package.pkgname,
                                                     package.version))):
            bpo.db.set_package_status(session, package,
                                      bpo.db.PackageStatus.built)
            bpo.ui.log_package(package, "missing_published_apk")

        # Missing built packages: change to "queued"
        if (package.status == bpo.db.PackageStatus.built and
            not os.path.exists("{}/{}-{}.apk".format(path_wip, package.pkgname,
                                                     package.version))):
            bpo.db.set_package_status(session, package,
                                      bpo.db.PackageStatus.queued)
            bpo.ui.log_package(package, "missing_built_apk")


def fix(limit_arch=None, limit_branch=None):
    """" Fix all inconsistencies between the database, the apk files on disk
         and the running jobs.
        :param limit_arch: architecture, e.g. "x86_64" (default: all)
        :param limit_branch: pmaports.git branch, e.g. "master"
                             (default: all) """
    branches = bpo.config.const.branches.keys()
    if limit_branch:
        branches = [limit_branch]

    logging.info("Fixing inconsistencies between DB and files on disk")
    for branch in branches:
        arches = bpo.config.const.branches[branch]["arches"]
        if limit_arch:
            arches = [limit_arch]
        for arch in arches:
            path_final = bpo.repo.final.get_path(arch, branch)
            path_wip = bpo.repo.wip.get_path(arch, branch)

            # Iterate over apks in wip and final repo
            logging.info(branch + "/" + arch + ": fix WIP apks vs DB status")
            fix_disk_vs_db(arch, branch, path_wip,
                           bpo.db.PackageStatus.built, True)
            logging.info(branch + "/" + arch + ": fix final apks vs DB status")
            fix_disk_vs_db(arch, branch, path_final,
                           bpo.db.PackageStatus.published)
            bpo.repo.wip.update_apkindex(arch, branch)

            # Iterate over packages in db
            logging.info(branch + "/" + arch + ": fix DB status vs apks")
            fix_db_vs_disk(arch, branch)

    # Fix running job status
    bpo.helpers.job.update_status()
