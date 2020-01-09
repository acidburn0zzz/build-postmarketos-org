# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Various tests, that need longer than the default timeout to run. Put them
    all here, so we can run the fast tests first and possibly see them fail
    rather quickly. In this file, place the faster tests at the top. """
import pytest

import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


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
def test_build_final_repo_with_two_pkgs_SLOW_45s(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger job-callback/get-depends and let it run all the way until the
        # final repository is ready to be published
        monkeypatch.setattr(bpo.repo.final, "publish", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends()

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
