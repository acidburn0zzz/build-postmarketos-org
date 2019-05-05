from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.helpers.config as config

gitlab = Blueprint('gitlab', __name__)


@gitlab.route('/api/pull-hook/gitlab')
@header_auth('X-Gitlab-Token', config.gitlab_secret)
def gitlab_pull():
    payload = request.get_json()
