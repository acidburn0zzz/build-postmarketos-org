# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/__init__.py """
import logging
import threading
import time

import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.repo


def test_build_thread_safety(monkeypatch):
    """
    Verify that bpo.repo.build doesn't run more than once at a time, even if
    both MainThread and ImageTimerThread happen to call it at the same time.
    Expected timeline:

    ImageTimerThread |..|bb|bb|bb|..|ww|ww|bb|bb|bb|..|ww|ww|
    MainThread       |..|..|ww|ww|bb|bb|bb|..|..|ww|bb|bb|bb|
                     |--|--|--|--|--|--|--|--|--|--|--|--|--|>time in 0.01s
                     00 01 02 03 04 05 06 07 08 09 10 11 12 13

    |..|: time.sleep in MainThread / timer interval sleep in ImageTimerThread
    |bb|: running bpo.repo.build (build_dummy below)
    |ww|: waiting for bpo.repo.build due to lock

    If the lock did not work, the ImageTimerThread would run not just two, but
    three times (take out the |ww| blocks). Therefore the test shows that the
    function is thread safe.
    """
    bpo_test.BPOServer()

    # The order in which the threads run bpo.repo.build
    threads_expected = [
        "ImageTimerThread",
        "MainThread",
        "ImageTimerThread",
        "MainThread"
    ]
    threads = []

    def build_dummy(force_repo_update=False, no_repo_update=False):
        logging.info("build_dummy called")
        threads.append(threading.current_thread().name)
        time.sleep(0.03)

    monkeypatch.setattr(bpo.repo, "_build", build_dummy)
    monkeypatch.setattr(bpo.images.queue, "fill", bpo_test.nop)

    bpo.images.queue.timer_iterate(next_interval=0.01, repo_build=False)
    time.sleep(0.02)
    bpo.repo.build()
    time.sleep(0.02)
    bpo.repo.build()

    assert threads == threads_expected

    bpo.images.queue.timer_stop()


def test_repo_is_apk_origin_in_db(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    # Origin exists in db with same version
    func = bpo.repo.is_apk_origin_in_db
    arch = "x86_64"
    branch = "master"
    apk_path = (bpo.config.const.top_dir +
                "/test/testdata/hello-world-wrapper-subpkg-1-r2.apk")
    session = bpo.db.session()
    assert func(session, arch, branch, apk_path) is True

    # Change version of origin
    origin_pkgname = "hello-world-wrapper"
    package = bpo.db.get_package(session, origin_pkgname, arch, branch)
    package.version = "9999-r0"
    session.merge(package)
    session.commit()

    # Origin exists in db, but with different version
    assert func(session, arch, branch, apk_path) is False

    # Delete package from db
    session.delete(package)
    session.commit()
    assert bpo.db.get_package(session, origin_pkgname, arch, branch) is None

    # Origin not found in db
    assert func(session, arch, branch, apk_path) is False


def test_build_arch_branch(monkeypatch):
    """ Test all code paths of bpo.repo.build_arch_branch(). Create the usual
        test database with the two hello-world and hello-world-wrapper
        packages, then let it build one package after another. When called
        again, it must figure out, that the WIP repo is complete and start to
        create the symlink repo. Also test the case, where the repo is stuck
        (hello-world failed, but -wrapper depends on it and can't be built).
    """
    # Disable retry_count code path (tested separately)
    monkeypatch.setattr(bpo.config.const, "retry_count_max", 0)

    # *** Monkeypatch functions ***
    # bpo.jobs.build_package.run
    global build_package_run_called
    global expected_pkgname

    def build_package_run(arch, pkgname, branch):
        global build_package_run_called
        global expected_pkgname
        build_package_run_called = True
        assert pkgname == expected_pkgname
        return True
    monkeypatch.setattr(bpo.jobs.build_package, "run", build_package_run)

    # bpo.repo.set_stuck
    global build_repo_stuck
    build_repo_stuck = False

    def bpo_repo_set_stuck(arch, branch):
        global build_repo_stuck
        build_repo_stuck = True
    monkeypatch.setattr(bpo.repo, "set_stuck", bpo_repo_set_stuck)

    # bpo.repo.symlink.create
    global bpo_symlink_create_called

    def bpo_repo_symlink_create(arch, branch, force):
        global bpo_symlink_create_called
        bpo_symlink_create_called = True
    monkeypatch.setattr(bpo.repo.symlink, "create", bpo_repo_symlink_create)

    # *** Prepare test ***
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    # Function and arguments variables
    session = bpo.db.session()
    slots_available = 1
    arch = "x86_64"
    branch = "master"
    func = bpo.repo.build_arch_branch

    # *** Test building all packages successfully ***
    # Start building "hello-world" (1/2)
    build_package_run_called = False
    expected_pkgname = "hello-world"
    assert func(session, slots_available, arch, branch) == 1
    assert build_package_run_called
    assert build_repo_stuck is False

    # Change "hello-world" to built
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)

    # Start building "hello-world-wrapper" (2/2)
    build_package_run_called = False
    expected_pkgname = "hello-world-wrapper"
    assert func(session, slots_available, arch, branch) == 1
    assert build_package_run_called
    assert build_repo_stuck is False

    # Change "hello-world-wrapper" to built (all packages are built!)
    package = bpo.db.get_package(session, "hello-world-wrapper", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)

    # Create symlink repo
    build_package_run_called = False
    bpo_symlink_create_called = False
    assert func(session, slots_available, arch, branch) == 0
    assert build_package_run_called is False
    assert bpo_symlink_create_called
    assert build_repo_stuck is False

    # *** Test repo being stuck ***
    # Change "hello-world" to failed
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.failed)

    # Change "hello-world-wrapper" to queued
    package = bpo.db.get_package(session, "hello-world-wrapper", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.queued)

    # Expect build_repo_stuck log message
    build_package_run_called = False
    bpo_symlink_create_called = False
    assert func(session, slots_available, arch, branch) == 0
    assert build_package_run_called is False
    assert bpo_symlink_create_called is False
    assert build_repo_stuck is True

    # *** Test repo being stuck (depend is building) ***
    # Change "hello-world" to building
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.building)

    # Expect build_repo_stuck log message
    build_package_run_called = False
    bpo_symlink_create_called = False
    assert func(session, slots_available, arch, branch) == 0
    assert build_package_run_called is False
    assert bpo_symlink_create_called is False
    assert build_repo_stuck is True


def test_repo_next_package_to_build(monkeypatch):
    # Disable retry_count code path (tested separately)
    monkeypatch.setattr(bpo.config.const, "retry_count_max", 0)

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    session = bpo.db.session()
    func = bpo.repo.next_package_to_build
    arch = "x86_64"
    branch = "master"

    # First package should be "hello-world"
    assert func(session, arch, branch) == "hello-world"

    # Change "hello-world" to failed
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.failed)

    # Remaining "hello-world-wrapper" depends on failing package "hello-world"
    assert func(session, arch, branch) is None
