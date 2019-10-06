# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


def test_callback_repo_missing_to_nop(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger job-callback/get-repo-missing
        monkeypatch.setattr(bpo.repo, "build", bpo_test.finish)
        bpo_test.trigger.job_callback_get_repo_missing()


def test_callback_repo_missing_to_build_two_pkgs(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger job-callback/get-repo-missing and let it run all the way
        # until the final repository is ready to be published
        monkeypatch.setattr(bpo.repo.final, "publish", bpo_test.finish)
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

# FIXME: test all kinds of errors, e.g. invalid push id
