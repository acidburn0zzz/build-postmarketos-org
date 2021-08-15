# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/jobs/build_package.py """
import bpo_test  # noqa
import bpo_test.trigger
import bpo.config.const
import bpo.helpers.job
import bpo.jobs.build_package
import bpo.worker.queue

import logging


def test_do_build_strict(monkeypatch):
    monkeypatch.setattr(bpo.config.const, "no_build_strict", ["gcc*-*"])
    func = bpo.jobs.build_package.do_build_strict

    assert func("gcc-armhf") is False
    assert func("gcc4-aarch64") is False
    assert func("gcc6-armv7") is False

    assert func("gcc") is True
    assert func("hello-world") is True


def test_retry_build(monkeypatch):
    """ High level test for the retry_count logic """
    global job_run_fake_count
    job_run_fake_count = 0

    def job_run_fake(name, note, tasks, branch, arch, pkgname, version):
        global job_run_fake_count

        job_run_fake_count += 1
        logging.info("job_run_fake_count: " + str(job_run_fake_count))

        assert name == "build_package"
        assert branch == "master"
        assert arch == "x86_64"
        assert pkgname == "hello-world"
        assert version == "1-r4"
        assert job_run_fake_count < 3

        return 1234

    monkeypatch.setattr(bpo.helpers.job, "run", job_run_fake)
    monkeypatch.setattr(bpo.config.const, "retry_count_max", 1)
    monkeypatch.setattr(bpo.repo, "set_stuck", bpo_test.stop_server)

    pkgname = "hello-world"
    with bpo_test.BPOServer():
        # Fill the db with "hello-world", "hello-world-wrapper" and let the bpo
        # server start building "hello-world". The actual building is prevented
        # in this test by the job_run_fake() override above.
        bpo_test.trigger.job_callback_get_depends("master")
        bpo.worker.queue.wait_until_empty()
        bpo_test.assert_package(pkgname, status="building", retry_count=0,
                                job_id=1234)
        assert job_run_fake_count == 1

        # Pretend that the build failed: call api/public/update-job-status,
        # just like sourcehut would do it. The bpo server then calls
        # bpo.helpers.jobs.update_status(), which reports a job
        # failure for the local job service. The bpo server starts the next
        # build. job_run_fake() gets called again and stops the bpo server.
        bpo_test.trigger.public_update_job_status()
        bpo_test.assert_package(pkgname, status="building", retry_count=1)
        assert job_run_fake_count == 2

        # Pretend that the build failed again. Now retry_count_max=1 is
        # reached, and the other package in the db, hello-world-wrapper,
        # depends on the failed package hello-world. The repo is stuck.
        # This will stop the server (see monkeypatch above).
        bpo_test.trigger.public_update_job_status()

    bpo_test.assert_package(pkgname, status="failed", retry_count=1)
    assert job_run_fake_count == 2
