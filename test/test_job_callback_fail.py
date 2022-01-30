# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.api.job_callback
import bpo.repo


bpo_repo_build_count = None


def test_callback_fail_build_package(monkeypatch):
    """ Trigger job-callback/get-depends, so the db gets filled with the
        hello-world and hello-world-wrapper packages, and bpo tries to build
        both of them. Fail building hello-world, let the local job service send
        the fail request, and finish the test when the bpo server tries to
        build the next package. """
    bpo_repo_build_orig = bpo.repo.build

    with bpo_test.BPOServer():
        global bpo_repo_build_count
        bpo_repo_build_count = 0

        # Fail the build
        monkeypatch.setattr(bpo.job_services.local.LocalJobServiceThread,
                            "run_print", bpo_test.raise_exception)

        def bpo_repo_build_fake(force_repo_update=False):
            global bpo_repo_build_count

            bpo_repo_build_count += 1
            if bpo_repo_build_count < 2:
                return bpo_repo_build_orig(force_repo_update)
            return bpo_test.stop_server()

        # Stop server when trying to build the package for the second time
        monkeypatch.setattr(bpo.repo, "build", bpo_repo_build_fake)

        # Fill db and try to build hello-world
        bpo_test.trigger.job_callback_get_depends("master")

    # Check package status
    bpo_test.assert_package("hello-world", status="failed")
