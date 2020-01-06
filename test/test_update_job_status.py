# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/api/public/update_job_status.py """
import requests

import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.jobs.build_package


def test_public_update_job_status(monkeypatch):
    arch = "x86_64"
    branch = "master"
    pkgname = "hello-world"
    pkgname2 = "second-package"
    version = "1-r4"

    # Expect the bpo server to build "second-package" and exit the bpo server
    # as soon as it tries to do that
    def fake_build_package(arch, pkgname, branch):
        if pkgname == "second-package":
            print("bpo server tries to build expected package")
            bpo_test.stop_server()
        else:
            print("bpo server tries to build something else: " + str(pkgname))
            bpo_test.stop_server_nok()
        # Fake job ID
        return 1337
    monkeypatch.setattr(bpo.jobs.build_package, "run", fake_build_package)

    with bpo_test.BPOServer():
        # Add "hello-world" package to DB, status: building
        session = bpo.db.session()
        package = bpo.db.Package(arch, branch, pkgname, version)
        package.status = bpo.db.PackageStatus.building
        session.merge(package)

        # Add "second-package" to DB, status: queued
        package2 = bpo.db.Package(arch, branch, pkgname2, version)
        session.merge(package2)
        session.commit()

        # Call update-job-status to set "hello-world" status to "failed" and
        # to start building "second-package"
        requests.post("http://127.0.0.1:5000/api/public/update-job-status")

    # Verify package status
    bpo_test.assert_package(pkgname, status="failed")
