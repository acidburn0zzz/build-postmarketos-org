from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.helpers.config as config
import bpo.jobs.get_depends

gitlab = Blueprint('gitlab', __name__)


@gitlab.route('/api/pull-hook/gitlab')
@header_auth('X-Gitlab-Token', config.gitlab_secret)
def gitlab_pull():
    payload = request.get_json()
    if payload["object_kind"] != "push":
        abort(400, 'Unknown object_kind')

    # TODO: Logging

    bpo.jobs.get_depends.run()
    return 'Triggered!'
