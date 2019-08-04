# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import flask
import bpo.config.const
import bpo.db

blueprint = flask.Blueprint("bpo_api", __name__)

def get_header(request, key):
    header = "X-BPO-" + key
    if header not in request.headers:
        raise ValueError("missing " + header + " header!")
    return request.headers[header]


def get_arch(request):
    """ Get architecture from X-BPO-Arch header and validate it. """
    arch = get_header(request, "Arch")
    if arch not in bpo.config.const.architectures:
        raise ValueError("invalid X-BPO-Arch: " + arch)
    return arch


def get_push(session, request):
    """ Get the push ID from X-BPO-Push-Id header and load the Push object from
        the database. """
    push_id = get_header(request, "Push-Id")
    result = session.query(bpo.db.Push).filter_by(id=int(push_id)).all()
    if not len(result):
        raise ValueError("invalid X-BPO-Push-Id: " + push_id)
    return result[0]


def get_package(session, request):
    pkgname = get_header(request, "Pkgname")
    arch = get_arch(request)
    ret = bpo.db.get_package(session, pkgname, arch)
    if not ret:
        raise ValueError("no package found with: pkgname=" + pkgname +
                         ", arch=" + arch)
    return ret


def get_version(request, package):
    version = get_header(request, "Version")
    if version != package.version:
        raise ValueError("version " + version + " submitted in the callback is"
                         " different from the package version in the db: " +
                         package + " (this probably is an outdated build job"
                         " that was not stopped after a new version of the"
                         " aport had been pushed?)")
    return version
