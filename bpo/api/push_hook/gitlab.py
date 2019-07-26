# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.jobs.get_repo_missing
import bpo.api
import bpo.db

blueprint = bpo.api.blueprint


@blueprint.route("/api/push-hook/gitlab", methods=["POST"])
@header_auth("X-Gitlab-Token", "push_hook_gitlab")
def push_hook_gitlab():
    payload = request.get_json()
    if payload["object_kind"] != "push":
        abort(400, "Unknown object_kind")

    # Insert push and commits
    session = bpo.db.session()
    push = bpo.db.Push()
    session.add(push)
    for commit_gitlab in payload["commits"]:
        commit = bpo.db.Commit(ref=commit_gitlab["id"],
                               message=commit_gitlab["message"],
                               push=push)
        session.add(commit)

    # Insert log message
    log = bpo.db.Log(action="push_hook", payload=payload, push=push)
    session.add(log)
    session.commit()

    # Run repo_missing job for all arches
    for arch in bpo.config.const.architectures:
        bpo.jobs.get_repo_missing.run(push.id, arch)

    return "Triggered!"
