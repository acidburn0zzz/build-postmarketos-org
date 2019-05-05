from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth

gitlab = Blueprint('gitlab', __name__)


@gitlab.route('/api/pull-hook/gitlab')
@header_auth('X-Gitlab-Token', 'pizza')
def gitlab_pull():
    payload = request.get_json()
