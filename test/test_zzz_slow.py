# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Various tests, that need longer than the default timeout to run. Put them
    all here, so we can run the fast tests first and possibly see them fail
    rather quickly. In this file, place the faster tests at the top. """
import pytest

import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


@pytest.mark.timeout(20)
def test_repo_missing_SLOW_20s(monkeypatch):
    """ Trigger the api push hook, then let bpo run the repo_missing job.
        Monkeypatch bpo.repo.build, so it stops after receiving repo_missing
        and does not try to build the repo. """
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.push_hook_gitlab()


@pytest.mark.timeout(45)
def test_build_final_repo_with_two_pkgs_SLOW_45s(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger job-callback/get-repo-missing and let it run all the way
        # until the final repository is ready to be published
        monkeypatch.setattr(bpo.repo.final, "publish", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    # WIP repo must be empty
    arch = "x86_64"
    branch = "master"
    path = bpo.repo.wip.get_path(arch, branch)
    apks = bpo.repo.get_apks(arch, branch, path)
    assert(apks == [])

    # Final repo must have both packages
    path = bpo.repo.final.get_path(arch, branch)
    apks = bpo.repo.get_apks(arch, branch, path)
    assert(apks == ["hello-world-1-r4.apk", "hello-world-wrapper-1-r2.apk"])
