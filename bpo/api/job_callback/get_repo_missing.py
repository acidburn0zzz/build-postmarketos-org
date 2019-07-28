# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.repo

blueprint = bpo.api.blueprint


def get_arch(request):
    """ Get architecture from X-BPO-Arch header and validate it. """
    if "X-BPO-Arch" not in request.headers:
        raise ValueError("missing X-BPO-Arch header!")
    arch = request.headers["X-BPO-Arch"]
    if arch not in bpo.config.const.architectures:
        raise ValueError("invalid X-BPO-Arch: " + arch)


def get_push(session, request):
    """ Get the push ID from X-BPO-Push-Id header and load the Push object from
        the database. """
    if "X-BPO-Push-Id" not in request.headers:
        raise ValueError("missing X-BPO-Push-Id header!")
    push_id = request.headers["X-BPO-Push-Id"]
    result = session.query(bpo.db.Push).filter_by(id=int(push_id)).all()
    if not len(result):
        raise ValueError("invalid X-BPO-Push-Id: " + push_id)
    return result[0]


def get_payload(request):
    """ Get the payload from the POST-data and verify it. """
    ret = request.get_json()

    # Check for duplicate pkgnames
    found = {}
    for package in ret:
        pkgname = package["pkgname"]
        if pkgname in found:
            raise RuntimeError("pkgname found twice in payload: " + pkgname)
        found[pkgname] = True

    return ret


def update_or_insert_packages(session, payload, arch):
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
        package_db = bpo.db.get_package(session, pkgname, arch)
        if package_db:
            if package_db.version != version:
                bpo.jobs.build_package.abort(arch, pkgname)
            package_db.version = version
            package_db.repo = repo
        else:
            package_db = bpo.db.Package(arch, pkgname, version)
        session.merge(package_db)


def update_package_depends(session, payload, arch):
    for package in payload:

        # Build list of dependencies (DB objects)
        depends = []
        for pkgname in package["depends"]:

            # Avoid complexity by only storing postmarketOS dependencies (which
            # are all in the database at this point), and ignoring Alpine
            # depends.
            depend = bpo.db.get_package(session, pkgname, arch)
            if depend:
                depends.append(depend)

        # Write changes
        package_db = bpo.db.get_package(session, package["pkgname"], arch)
        package_db.depends = depends
        session.merge(package_db)


@blueprint.route("/api/job-callback/get-repo-missing", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_get_repo_missing():
    # Parse input data
    arch = get_arch(request)
    payload = get_payload(request)
    session = bpo.db.session()
    push = get_push(session, request)

    # Update packages in DB
    update_or_insert_packages(session, payload, arch)
    update_package_depends(session, payload, arch)

    # Write log entry
    log = bpo.db.Log(action="job_callback_get_repo_missing", payload=payload,
                     push=push, arch=arch)
    session.add(log)
    session.commit()
    bpo.repo.build(arch)
    
    return "warming up build servers..."
