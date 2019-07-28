# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db

blueprint = bpo.api.blueprint


@blueprint.route("/api/job-callback/build-package", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_build_package():
    # FIXME
    logging.info("STUB: job_callback_build_package")

    # TODO:
    # * save file to disk
    # * get queue_id from handler
    # * only mark as BUILT, if this was the last file (do we send multiple?)
    queue_id = 1
    queue_entry = bpo.helpers.queue.get_entry_by_id(queue_id)
    if not queue_entry:
        raise RuntimeError("invalid queue_id. FIXME: return error to user!")

    # FIXME: set package status: BUILT
    # FIXME: update package index
    bpo.repo.build(arch)

    return "package received, kthxbye"
