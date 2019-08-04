# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db

blueprint = bpo.api.blueprint


@blueprint.route("/api/job-callback/build-package", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_build_package():
    session = bpo.db.session()
    package = bpo.api.get_package(session, request)
    version = bpo.api.get_version(request, package)

    # TODO:
    # * save files to disk

    # Change status to built
    package.status = bpo.db.PackageStatus.built
    session.merge(package)
    session.commit()

    # Build next package / update index
    # FIXME: commented out, because it crashes at comparing status values
    # bpo.repo.build(package.arch)
    return "package received, kthxbye"
