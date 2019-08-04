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
    arch = bpo.api.get_arch(request)

    # TODO:
    # * verify that we wanted to build this package
    # * save files to disk
    # * set package status: BUILT
    # * update package index
    # * bpo.repo.build(arch)

    return "package received, kthxbye"
