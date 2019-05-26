from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.jobs.get_depends
import bpo.db

gitlab = Blueprint('gitlab', __name__)


@gitlab.route('/api/push-hook/gitlab', methods=['POST'])
@header_auth('X-Gitlab-Token', 'push_hook_gitlab')
def gitlab_pull():
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

    bpo.jobs.get_depends.run(push.id)
    return 'Triggered!'
