# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import pathlib
import re
from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db

blueprint = bpo.api.blueprint


def get_apks(request):
    """ Get all attached apks and verify the file names. """
    pattern = re.compile("^[a-z0-9._-]+.apk$")
    ret = request.files.getlist("file[]")

    for apk in ret:
        if not pattern.match(apk.filename):
            raise RuntimeError("Invalid filename: " + apk.filename)

    return ret


@blueprint.route("/api/job-callback/build-package", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_build_package():
    session = bpo.db.session()
    package = bpo.api.get_package(session, request)
    version = bpo.api.get_version(request, package)
    apks = get_apks(request)

    # Create staging dir
    staging = (bpo.config.args.repo_staging_path + "/" + package.branch + "/" +
               package.arch)
    pathlib.Path(staging).mkdir(0o755, True, True)

    # Save files to disk
    for apk in apks:
        path = staging + "/" + apk.filename
        logging.info("Saving " + path)
        apk.save(path)

    # Change status to built
    package.status = bpo.db.PackageStatus.built
    session.merge(package)
    session.commit()

    # Build next package or publish repo after building all waiting packages
    bpo.repo.build(package.arch, package.branch)
    return "package received, kthxbye"
