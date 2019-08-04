# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import flask
import bpo.config.const
import bpo.db

blueprint = flask.Blueprint("bpo_api", __name__)


def get_arch(request):
    """ Get architecture from X-BPO-Arch header and validate it. """
    if "X-BPO-Arch" not in request.headers:
        raise ValueError("missing X-BPO-Arch header!")
    arch = request.headers["X-BPO-Arch"]
    if arch not in bpo.config.const.architectures:
        raise ValueError("invalid X-BPO-Arch: " + arch)
    return arch


def get_push(session, request):
    """ Get the push ID from X-BPO-Push-Id header and load the Push object from
        the database. """
    if "X-BPO-Push-Id" not in request.headers:
        raise ValueError("missing X-BPO-Push-Id header!")
    push_id = request.headers["X-BPO-Push-Id"]
    result = session.query(bpo.db.Push).filter_by(id=int(push_id)).all()
    if not len(result):
        raise ValueError("invalid X-BPO-Push-Id: " + push_id)
    return result[0]
