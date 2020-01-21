# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Various tests, that need longer than the default timeout to run. Put them
    all here, so we can run the fast tests first and possibly see them fail
    rather quickly. In this file, place the faster tests at the top. """
import os
import pytest
import shutil

import bpo_test
import bpo_test.const
import bpo_test.trigger
import bpo.config.const
import bpo.db
import bpo.jobs
import bpo.repo
import bpo.repo.final


@pytest.mark.timeout(20)
def test_remove_deleted_package_SLOW_20s(monkeypatch):
    # Only one arch, so the bpo server doesn't attempt to run multiple repo
    # indexing jobs at once. This doesn't work with the local job service.
    monkeypatch.setattr(bpo.config.const, "architectures", ["x86_64"])

    # Stop server when it would publish the packages
    monkeypatch.setattr(bpo.repo.final, "publish", bpo_test.stop_server)

    with bpo_test.BPOServer():
        # Put test apks in final repo
        arch = "x86_64"
        branch = "master"
        final_path = bpo.repo.final.get_path(arch, branch)
        testdata = bpo.config.const.top_dir + "/test/testdata/"
        os.makedirs(final_path, exist_ok=True)
        for apk in ["hello-world-1-r3.apk",  # wrong version
                    "hello-world-1-r4.apk",
                    "hello-world-wrapper-1-r2.apk"]:
            shutil.copy(testdata + "/" + apk, final_path + "/" + apk)

        # Put into db: hello-world, hello-world-wrapper
        session = bpo.db.session()
        published = bpo.db.PackageStatus.published
        session.merge(bpo.db.Package(arch, branch, "hello-world", "1-r4",
                                     published))
        session.merge(bpo.db.Package(arch, branch, "hello-world-wrapper",
                                     "1-r2", published))
        session.commit()

        # pmaports.git only has "hello-world", not "hello-world-wrapper"
        payload = "depends.master.x86_64_hello-world_only.json"
        bpo_test.trigger.job_callback_get_depends(payload)

    # Check if database was updated properly
    bpo_test.assert_package("hello-world", status="published", version="1-r4")
    bpo_test.assert_package("hello-world-wrapper", exists=False)

    # Check if packages were removed properly
    assert os.path.exists(final_path + "/hello-world-1-r4.apk")
    assert not os.path.exists(final_path + "/hello-world-1-r3.apk")
    assert not os.path.exists(final_path + "/hello-world-wrapper-1-r2.apk")

    # Check if APKINDEX was created for final repo
    assert os.path.exists(final_path + "/APKINDEX.tar.gz")


@pytest.mark.timeout(40)
def test_depends_SLOW_40s(monkeypatch):
    """ Trigger the api push hook, then let bpo run the depends job.
        Monkeypatch bpo.repo.build, so it stops after receiving depends
        and does not try to build the repo. """

    # Limit to two arches (more would increase test time)
    monkeypatch.setattr(bpo.config.const, "architectures", ["x86_64", "armv7"])

    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.push_hook_gitlab()


@pytest.mark.timeout(45)
def test_build_final_repo_with_two_pkgs_SLOW_45s(monkeypatch, tmpdir):
    # Prepare job-callback/get-depends payload
    payload_path = str(tmpdir) + "/payload.json"
    v_hello = bpo_test.const.version_hello_world
    v_wrapper = bpo_test.const.version_hello_world_wrapper
    overrides = {"hello-world": {"version": v_hello},
                 "hello-world-wrapper": {"version": v_wrapper}}
    bpo_test.trigger.override_depends_json(payload_path, overrides)

    with bpo_test.BPOServer():
        # Trigger job-callback/get-depends and let it run all the way until the
        # final repository is ready to be published
        monkeypatch.setattr(bpo.repo.final, "publish", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends(payload_path=payload_path)

    # WIP repo must be empty
    arch = "x86_64"
    branch = "master"
    path = bpo.repo.wip.get_path(arch, branch)
    apks = bpo.repo.get_apks(arch, branch, path)
    assert(apks == [])

    # Final repo must have both packages
    path = bpo.repo.final.get_path(arch, branch)
    apks = bpo.repo.get_apks(arch, branch, path)
    assert(apks == ["hello-world-" + v_hello + ".apk",
                    "hello-world-wrapper-" + v_wrapper + ".apk"])
