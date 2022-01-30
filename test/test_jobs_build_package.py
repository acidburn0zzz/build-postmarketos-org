# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/jobs/build_package.py """
import os
import shutil

import bpo_test
import bpo_test.trigger
import bpo.repo.wip
import bpo.jobs.build_package


def test_build_package_run_skip_existing(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    # Package status should be "queued"
    session = bpo.db.session()
    pkgname = "hello-world"
    arch = "x86_64"
    branch = "master"
    package = bpo.db.get_package(session, pkgname, arch, branch)
    assert package.status == bpo.db.PackageStatus.queued

    # Copy hello-world apk to wip repo
    testdata_path = bpo.config.const.top_dir + "/test/testdata/"
    apk_hello = testdata_path + "/hello-world-1-r4.apk"
    wip_path = bpo.repo.wip.get_path(arch, branch)
    os.makedirs(wip_path)
    shutil.copy(apk_hello, wip_path)

    # Build should be skipped
    assert bpo.jobs.build_package.run(arch, pkgname, branch) is False
    bpo_test.assert_package(pkgname, status="built")
