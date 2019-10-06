# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.api.job_callback
import bpo.repo


def test_callback_fail_build_package(monkeypatch):
    """ Trigger job-callback/get-repo-missing, so the db gets filled with the
        hello-world and hello-world-wrapper packages, and bpo tries to build
        both of them. Fail building hello-world, let the local job service send
        the fail request, and finish the test when the bpo server tries to
        build the next package. """

    with bpo_test.BPOServer():
        # Fail the build
        monkeypatch.setattr(bpo.job_services.local.LocalJobServiceThread,
                            "run_print", bpo_test.raise_exception)

        # Finish build instead of trying to build the next package
        monkeypatch.setattr(bpo.api.job_callback.fail,
                            "job_callback_fail_continue_build_package",
                            bpo_test.finish)

        # Fill db and try to build hello-world
        bpo_test.trigger.job_callback_get_repo_missing()

    # Check package status
    session = bpo.db.session()
    package = bpo.db.get_package(session, "hello-world", "x86_64", "master")
    assert(package.status == bpo.db.PackageStatus.failed)
