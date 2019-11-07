# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/api/public/update_job_status.py """
import requests

import bpo_test
import bpo_test.trigger
import bpo.db


def test_public_update_job_status(monkeypatch):
    arch = "x86_64"
    branch = "master"
    pkgname = "hello-world"
    version = "1-r4"

    with bpo_test.BPOServer():
        # Add "hello-world" package to DB, status: building
        session = bpo.db.session()
        package = bpo.db.Package(arch, branch, pkgname, version)
        package.status = bpo.db.PackageStatus.building
        session.merge(package)
        session.commit()

        # Call update-job-status, verify status: failed
        requests.post("http://127.0.0.1:5000/api/public/update-job-status")
        bpo_test.assert_package(pkgname, status="failed")

        bpo_test.stop_server()
