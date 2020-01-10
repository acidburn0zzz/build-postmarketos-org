# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/__init__.py """
import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.repo


def test_repo_is_apk_origin_in_db(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends()

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

    # bpo.ui.log
    global expected_log_action
    global expected_log_action_found
    expected_log_action = "build_repo_stuck"
    expected_log_action_found = False

    def bpo_ui_log(action, *args, **kwargs):
        global expected_log_action
        global expected_log_action_found
        print("bpo_ui_log: args: {}, kwargs: {}".format(str(args),
                                                        str(kwargs)))
        if action == expected_log_action:
            expected_log_action_found = True
    monkeypatch.setattr(bpo.ui, "log", bpo_ui_log)

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
        bpo_test.trigger.job_callback_get_depends()

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
    assert(func(session, slots_available, arch, branch) == 1)
    assert(build_package_run_called)
    assert(expected_log_action_found is False)

    # Change "hello-world" to built
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)

    # Start building "hello-world-wrapper" (2/2)
    build_package_run_called = False
    expected_pkgname = "hello-world-wrapper"
    assert(func(session, slots_available, arch, branch) == 1)
    assert(build_package_run_called)
    assert(expected_log_action_found is False)

    # Change "hello-world-wrapper" to built (all packages are built!)
    package = bpo.db.get_package(session, "hello-world-wrapper", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)

    # Create symlink repo
    build_package_run_called = False
    bpo_symlink_create_called = False
    assert(func(session, slots_available, arch, branch) == 0)
    assert(build_package_run_called is False)
    assert(bpo_symlink_create_called)
    assert(expected_log_action_found is False)

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
    expected_log_action_found = False
    assert(func(session, slots_available, arch, branch) == 0)
    assert(build_package_run_called is False)
    assert(bpo_symlink_create_called is False)
    assert(expected_log_action_found)


def test_repo_next_package_to_build(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends()

    session = bpo.db.session()
    func = bpo.repo.next_package_to_build
    arch = "x86_64"
    branch = "master"

    # First package should be "hello-world"
    assert(func(session, arch, branch) == "hello-world")

    # Change "hello-world" to failed
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.failed)

    # Remaining "hello-world-wrapper" depends on failing package "hello-world"
    assert(func(session, arch, branch) is None)
