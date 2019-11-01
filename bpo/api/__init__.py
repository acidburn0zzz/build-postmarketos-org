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


def get_branch(request):
    """ Get branch from X-BPO-Branch header and validate it. """
    branch = get_header(request, "Branch")
    if branch not in bpo.config.const.branches:
        raise ValueError("invalid X-BPO-Branch: " + branch)
    return branch


def get_package(session, request):
    pkgname = get_header(request, "Pkgname")
    arch = get_arch(request)
    branch = get_branch(request)
    ret = bpo.db.get_package(session, pkgname, arch, branch)
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


def get_file(request, filename):
    """ :returns: werkzeug.datastructures.FileStorage object """
    for storage in request.files.getlist("file[]"):
        if storage.filename == filename:
            return storage
    raise ValueError("Missing file " + filename + " in payload.")
