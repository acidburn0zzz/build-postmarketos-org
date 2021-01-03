# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os

from flask import request
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.ui

blueprint = bpo.api.blueprint


def get_apks(request):
    """ Get all attached apks and verify the file names. """
    pattern = bpo.config.const.pattern_apk_name
    ret = request.files.getlist("file[]")

    for apk in ret:
        if not pattern.match(apk.filename):
            raise RuntimeError("Invalid filename: " + apk.filename)

    return ret


@blueprint.route("/api/job-callback/build-package", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_build_package():
    job_id = bpo.api.get_header(request, "Job-Id")
    session = bpo.db.session()
    package = bpo.api.get_package(session, request)
    apks = get_apks(request)

    # Create WIP dir
    wip = (bpo.config.args.repo_wip_path + "/" + package.branch + "/" +
           package.arch)
    os.makedirs(wip, exist_ok=True)

    # Save files to disk
    for apk in apks:
        path = wip + "/" + apk.filename
        logging.info("Saving " + path)
        apk.save(path)

    # Index and sign WIP APKINDEX
    bpo.repo.wip.update_apkindex(package.arch, package.branch)

    # Change status to built
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built,
                              job_id)

    bpo.ui.log_package(package, "api_job_callback_build_package")

    # Build next package or publish repo after building all queued packages
    bpo.repo.build()
    return "package received, kthxbye"
