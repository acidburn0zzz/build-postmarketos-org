# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


def test_callback_repo_missing_update_package(monkeypatch):
    # Stop bpo server after bpo.repo.build was called 2x
    global stop_count
    stop_count = 0

    def stop_count_increase(*args, **kwargs):
        global stop_count
        stop_count += 1
        print("stop_count_increase: " + str(stop_count))
        if stop_count == 2:
            bpo_test.finish()
    monkeypatch.setattr(bpo.repo, "build", stop_count_increase)

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        bpo_test.trigger.job_callback_get_repo_missing()

        # hello-world: decrease version, change status to failed
        session = bpo.db.session()
        pkgname = "hello-world"
        arch = "x86_64"
        branch = "master"
        package = bpo.db.get_package(session, pkgname, arch, branch)
        package.version = "0-r0"
        package.status = bpo.db.PackageStatus.failed
        session.merge(package)
        session.commit()

        # Fill the db with "hello-world", "hello-world-wrapper" again
        bpo_test.trigger.job_callback_get_repo_missing()

        # Check if updated properly
        package = bpo.db.get_package(session, pkgname, arch, branch)
        assert package.status == bpo.db.PackageStatus.queued
        assert package.version == "1-r4"


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
