# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
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


def get_pkgnames_commits(payload):
    """ Get modified pkgnames from changed (added, modified, removed) files in
        payload, along with the commit hashes where they were modified.
        :returns: dict like: {"hello-world": "d34dc4fef00", ...} """
    if "commits" not in payload:
        raise RuntimeError("Missing 'commits' key in payload")

    # Limitation by gitlab API: at most 20 commits are listed, even if more are
    # pushed. This is fine for our use case, since we only use the resulting
    # list to reset failed packages.
    # https://docs.gitlab.com/ee/user/project/integrations/webhooks.html

    ret = {}
    for commit in payload["commits"]:
        if "id" not in commit:
            raise RuntimeError(f"Missing 'id' key in commit: {commit}")
        for key in ["added", "modified", "removed"]:
            if key not in commit:
                raise RuntimeError(f"Missing '{key}' key in commit: {commit}")
            for path in commit[key]:
                if not path.endswith("/APKBUILD"):
                    continue
                # Name of directory with APKBUILD is pkgname
                pkgname = os.path.basename(os.path.dirname(path))
                if not pkgname:
                    continue
                if pkgname in ret:
                    continue
                ret[pkgname] = commit["id"]
    return ret


def reset_failed_packages(pkgnames_commits, branch):
    """ Reset failed packages, which might be fixed by the packages that were
        modified. These are the packages from the paramter and all packages
        that depend on them.
        :param pkgnames_commits: from get_pkgnames_commits()
    """
    def reset_failed_package(package, action, commit, depend_pkgname=None):
        package.status = bpo.db.PackageStatus.queued
        package.retry_count = 0
        session.merge(package)
        session.commit()

        bpo.ui.log_package(package, action, depend_pkgname, commit)

    session = bpo.db.session()
    failed = session.query(bpo.db.Package).\
        filter_by(status=bpo.db.PackageStatus.failed).\
        filter_by(branch=branch)

    for package in failed:
        if package.pkgname in pkgnames_commits:
            commit = pkgnames_commits[package.pkgname]
            reset_failed_package(package, "api_push_reset_failed", commit)
            continue

        for pkg_depend in package.depends:
            if pkg_depend.pkgname in pkgnames_commits:
                commit = pkgnames_commits[pkg_depend.pkgname]
                reset_failed_package(package, "api_push_reset_failed_depend",
                                     commit, depend_pkgname=pkg_depend.pkgname)
                break


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

    # Reset relevant failed packages
    pkgnames_commits = get_pkgnames_commits(payload)
    reset_failed_packages(pkgnames_commits, branch)

    # Run depends job for all arches
    bpo.jobs.get_depends.run(branch)

    return "Triggered!"
