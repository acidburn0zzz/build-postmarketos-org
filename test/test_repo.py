# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/__init__.py """
import requests

import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.repo


def test_repo_next_package_to_build(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.finish)
        bpo_test.trigger.job_callback_get_repo_missing()

    session = bpo.db.session()
    func = bpo.repo.next_package_to_build
    arch = "x86_64"
    branch = "master"

    # First package should be "hello-world"
    assert(func(session, arch, branch) == "hello-world")

    # Change "hello-world" to failed
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    package.status = bpo.db.PackageStatus.failed
    session.merge(package)

    # Remaining "hello-world-wrapper" depends on failing package "hello-world"
    assert(func(session, arch, branch) is None)
