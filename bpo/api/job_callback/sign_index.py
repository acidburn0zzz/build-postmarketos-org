# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db

blueprint = bpo.api.blueprint


@blueprint.route("/api/job-callback/sign-index", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_sign_index():
    # TODO:
    # * save index on disks
    # * get arch from handler
    arch = "x86_64"
    bpo.repo.publish(arch)

    return "alright, rollin' out the new repo"
