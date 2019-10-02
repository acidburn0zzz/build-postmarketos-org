# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.jobs.get_repo_missing
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
        # FIXME: write log message
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

    # FIXME: move to own function like get_branch and simply skip when unknown
    if payload["object_kind"] != "push":
        abort(400, "Unknown object_kind")

    # Insert push and commits
    session = bpo.db.session()
    push = bpo.db.Push(branch)
    session.add(push)
    for commit_gitlab in payload["commits"]:
        commit = bpo.db.Commit(ref=commit_gitlab["id"],
                               message=commit_gitlab["message"],
                               push=push)
        session.add(commit)
    session.commit()
    bpo.ui.log_and_update(action="api_push_hook_gitlab", payload=payload,
                          branch=push.branch)

    # Run repo_missing job for all arches
    for arch in bpo.config.const.architectures:
        bpo.jobs.get_repo_missing.run(push, arch)

    return "Triggered!"
