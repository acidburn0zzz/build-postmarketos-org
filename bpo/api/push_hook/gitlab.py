# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from flask import request, abort
from bpo.helpers.headerauth import header_auth
import bpo.jobs.get_depends
import bpo.api
import bpo.db

blueprint = bpo.api.blueprint


def get_branch(payload):
    """ Get branch from payload and validate it. """
    # Key must exist
    if "ref" not in payload:
        raise RuntimeError("Missing 'ref' key in payload")

    # It must start with "refs/heads/"
    prefix = "refs/heads/"
    if not payload["ref"].startswith(prefix):
        raise RuntimeError("'ref' does *not* start with '" + prefix + "': " +
                           payload["ref"])

    # Ignore non-configured branches
    branch = payload["ref"][len(prefix):]
    if branch not in bpo.config.const.branches:
        logging.info("NOTE: ignoring push for branch: " + branch)
        return None
    return branch


@blueprint.route("/api/push-hook/gitlab", methods=["POST"])
@header_auth("X-Gitlab-Token", "push_hook_gitlab")
def push_hook_gitlab():
    payload = request.get_json()
    branch = get_branch(payload)
    if not branch:
        return "Branch isn't relevant, doing nothing"

    if payload["object_kind"] != "push":
        abort(400, "Unknown object_kind")

    # Insert log entry
    bpo.ui.log("api_push_hook_gitlab", payload=payload, branch=branch)

    # Run depends job for all arches
    bpo.jobs.get_depends.run()

    return "Triggered!"
