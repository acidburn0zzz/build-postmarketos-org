# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import json
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


def get_payload(request, arch, branch):
    """ Get the get_depends callback specific payload from the POST-data
        and verify it. """
    filename = "depends." + branch + "." + arch + ".json"
    storage = bpo.api.get_file(request, filename)
    ret = json.loads(storage.read().decode("utf-8"))

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
                package_db.status = bpo.db.PackageStatus.queued
            package_db.version = version
            package_db.repo = repo
        else:
            package_db = bpo.db.Package(arch, branch, pkgname, version)
        session.merge(package_db)
    session.commit()


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
    session.commit()


def remove_deleted_packages_db(session, payload, arch, branch):
    """ Remove all packages from the database, that have been deleted from
        pmaports.git
        :returns: True if packages were deleted, False otherwise """
    ret = False

    # Sort payload by pkgname for faster lookups
    packages_payload = {}
    for package in payload:
        packages_payload[package["pkgname"]] = package

    # Iterate over packages in db
    packages_db = session.query(bpo.db.Package).filter_by(arch=arch,
                                                          branch=branch).all()
    for package_db in packages_db:
        # Keep entries, that are part of the depends payload
        if package_db.pkgname in packages_payload:
            continue

        ret = True
        bpo.ui.log_package(package_db, "package_removed_from_pmaports")

        # Delete package from db and commit this change, because we might write
        # to the log in the next iteration. If we don't commit and write to the
        # log, we get a "database is locked" error.
        session.delete(package_db)
        session.commit()
    return ret


@blueprint.route("/api/job-callback/get-depends", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_get_depends():
    # Parse input data
    job_id = bpo.api.get_header(request, "Job-Id")
    payloads = collections.OrderedDict()
    for branch in bpo.config.const.branches:
        if branch not in payloads:
            payloads[branch] = collections.OrderedDict()
        for arch in bpo.config.const.architectures:
            payloads[branch][arch] = get_payload(request, arch, branch)

    # Update packages in DB
    session = bpo.db.session()
    force_repo_update = False
    for branch, payload_arch in payloads.items():
        for arch, payload in payload_arch.items():
            update_or_insert_packages(session, payload, arch, branch)
            update_package_depends(session, payload, arch, branch)
            if remove_deleted_packages_db(session, payload, arch, branch):
                bpo.repo.wip.clean(arch, branch)
                # Delete obsolete apks in final repo
                force_repo_update = True

    bpo.ui.log("api_job_callback_get_depends", payload=payload,
               job_id=job_id)

    # Make sure that we did not miss any job status changes
    bpo.helpers.job.update_package_status()

    bpo.repo.build(force_repo_update)
    return "warming up build servers..."
