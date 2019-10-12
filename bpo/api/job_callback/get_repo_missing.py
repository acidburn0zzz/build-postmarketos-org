# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from flask import request
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.helpers.job
import bpo.repo
import bpo.repo.wip
import bpo.ui

blueprint = bpo.api.blueprint


def get_payload(request):
    """ Get the get_repo_missing callback specific payload from the POST-data
        and verify it. """
    ret = request.get_json()

    # Check for duplicate pkgnames
    found = {}
    for package in ret:
        pkgname = package["pkgname"]
        if pkgname in found:
            raise RuntimeError("pkgname found twice in payload: " + pkgname)
        found[pkgname] = True

    return ret


def update_or_insert_packages(session, payload, arch, branch):
    """ Update/insert packages from payload into the database, with all
        information except for the dependencies. These need to be set later,
        because that needs to happen after each package has an ID assigned.
        Otherwise we will get duplicates in the database (resulting in errors
        from the unique pkgname-arch index). """
    for package in payload:
        pkgname = package["pkgname"]
        version = package["version"]
        repo = package["repo"]

        # Find existing db entry if possible (update or insert logic)
        package_db = bpo.db.get_package(session, pkgname, arch, branch)
        if package_db:
            if package_db.version != version:
                bpo.jobs.build_package.abort(package_db)
            package_db.version = version
            package_db.repo = repo
            package_db.status = bpo.db.PackageStatus.queued
        else:
            package_db = bpo.db.Package(arch, branch, pkgname, version)
        session.merge(package_db)


def update_package_depends(session, payload, arch, branch):
    for package in payload:

        # Build list of dependencies (DB objects)
        depends = []
        for pkgname in package["depends"]:

            # Avoid complexity by only storing postmarketOS dependencies (which
            # are all in the database at this point), and ignoring Alpine
            # depends.
            depend = bpo.db.get_package(session, pkgname, arch, branch)
            if depend:
                depends.append(depend)

        # Write changes
        package_db = bpo.db.get_package(session, package["pkgname"], arch,
                                        branch)
        package_db.depends = depends
        session.merge(package_db)


def remove_deleted_packages(session, payload, arch, branch):
    """ Remove all packages from the database, that have been deleted from
        pmaports.git """
    # FIXME: this check is not good enough. We should be able to delete
    # packages that never made it into the final repository with this code, but
    # once they are there, they will be kept forever. In order to also delete
    # packages that made it into the final repository, but which are no longer
    # in the pmaports, we need a list of all packages in pmaports.git for the
    # given arch and branch. Right now we only have the packages that need to
    # be built.

    # Sort payload by pkgname for faster lookups
    packages_payload = {}
    for package in payload:
        packages_payload[package["pkgname"]] = package

    # Iterate over packages in db
    final_path = bpo.repo.final.get_path(arch, branch)
    packages_db = session.query(bpo.db.Package).filter_by(arch=arch,
                                                          branch=branch).all()
    for package_db in packages_db:
        # Keep entries, that are part of the repo_missing payload
        if package_db.pkgname in packages_payload:
            continue

        # Keep entries, where we have a binary package
        apk = "{}-{}.apk".format(package_db.pkgname, package_db.version)
        if os.path.exists(final_path + "/" + apk):
            continue

        bpo.ui.log_package(package_db, "package_removed_from_pmaports")
        session.delete(package_db)


@blueprint.route("/api/job-callback/get-repo-missing", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_get_repo_missing():
    # Parse input data
    arch = bpo.api.get_arch(request)
    branch = bpo.api.get_branch(request)
    payload = get_payload(request)
    session = bpo.db.session()

    # Update packages in DB
    update_or_insert_packages(session, payload, arch, branch)
    update_package_depends(session, payload, arch, branch)
    remove_deleted_packages(session, payload, arch, branch)
    session.commit()
    bpo.ui.log("api_job_callback_get_repo_missing", payload=payload, arch=arch,
               branch=branch)

    # Make sure that we did not miss any job status changes
    bpo.helpers.job.update_package_status()

    bpo.repo.wip.clean(arch, branch)
    bpo.repo.build()

    return "warming up build servers..."
