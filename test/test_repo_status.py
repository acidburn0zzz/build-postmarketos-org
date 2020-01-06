# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/status.py """
import bpo_test
import bpo_test.trigger
import bpo.config.const
import bpo.jobs.build_package
import os
import shutil


def test_is_apk_broken():
    func = bpo.repo.status.is_apk_broken
    assert func({"abuild_version": None}) is False
    assert func({"abuild_version": "3.5.0_rc1-r1"}) is False
    assert func({"abuild_version": "3.5.0_rc1-r0"}) is True


def test_remove_broken_apk_db(tmpdir, monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    func = bpo.repo.status.remove_broken_apk
    apk_path = str(tmpdir) + "/delete-me.apk"
    func = bpo.repo.status.remove_broken_apk
    session = bpo.db.session()
    arch = "x86_64"
    branch = "master"

    # Check if the apk was deleted
    shutil.copy(__file__, apk_path)
    func(session, "pkgname-not-in-db", "1.2-r0", arch, branch, apk_path)
    assert os.path.exists(apk_path) is False

    # Don't reset if package status (version differs)
    pkgname = "hello-world"
    version = "10-r0"
    package = bpo.db.get_package(session, pkgname, arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)
    shutil.copy(__file__, apk_path)
    func(session, pkgname, version, arch, branch, apk_path)
    bpo_test.assert_package(pkgname, status="built")

    # Reset package status to queued (version matches)
    pkgname = "hello-world"
    version = "1-r4"
    package = bpo.db.get_package(session, pkgname, arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)
    shutil.copy(__file__, apk_path)
    func(session, pkgname, version, arch, branch, apk_path)
    bpo_test.assert_package(pkgname, status="queued")

    # Don't reset depending package from to queued (status is not failed)
    pkgname_depending = "hello-world-wrapper"
    package_depending = bpo.db.get_package(session, pkgname_depending, arch,
                                           branch)
    bpo.db.set_package_status(session, package_depending,
                              bpo.db.PackageStatus.built)
    shutil.copy(__file__, apk_path)
    func(session, pkgname, version, arch, branch, apk_path)
    bpo_test.assert_package(pkgname_depending, status="built")

    # Don't reset non-depending package from to queued (status is failed)
    pkgname_non_depending = "postmarketos-base"
    version_non_depending = "1337-r0"
    package_non_depending = bpo.db.Package(arch, branch, pkgname_non_depending,
                                           version_non_depending)
    package_non_depending.status = bpo.db.PackageStatus.failed
    session.merge(package_non_depending)
    session.commit()
    bpo_test.assert_package(pkgname_non_depending, status="failed")
    shutil.copy(__file__, apk_path)
    func(session, pkgname, version, arch, branch, apk_path)
    bpo_test.assert_package(pkgname_non_depending, status="failed")

    # Reset depending package to queued (status is failed)
    package_depending = bpo.db.get_package(session, pkgname_depending, arch,
                                           branch)
    bpo.db.set_package_status(session, package_depending,
                              bpo.db.PackageStatus.failed)
    shutil.copy(__file__, apk_path)
    func(session, pkgname, version, arch, branch, apk_path)
    bpo_test.assert_package(pkgname_depending, status="queued")


def test_fix_disk_vs_db(monkeypatch):
    """ Test all code paths of bpo.repo.status.fix_disk_vs_db() """
    arch = "x86_64"
    branch = "master"
    testdata = bpo.config.const.top_dir + "/test/testdata/"
    func = bpo.repo.status.fix_disk_vs_db

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    # Final repo: add up-to-date hello-world
    final_path = bpo.repo.final.get_path(arch, branch)
    os.makedirs(final_path)
    shutil.copy(testdata + "/hello-world-1-r4.apk", final_path)

    # Fix hello-world: queued -> published
    bpo_test.assert_package("hello-world", status="queued")
    bpo_test.assert_package("hello-world-wrapper", status="queued")
    func(arch, branch, final_path, bpo.db.PackageStatus.published)
    bpo_test.assert_package("hello-world", status="published")
    bpo_test.assert_package("hello-world-wrapper", status="queued")

    # Wip repo: add hello-world-wrapper and obsolete hello-world
    wip_path = bpo.repo.wip.get_path(arch, branch)
    os.makedirs(wip_path)
    shutil.copy(testdata + "/hello-world-wrapper-1-r2.apk", wip_path)
    shutil.copy(testdata + "/hello-world-1-r3.apk", wip_path)

    # Fix hello-world-wrapper: queued -> built; remove obsolete apk
    bpo_test.assert_package("hello-world-wrapper", status="queued")
    func(arch, branch, wip_path, bpo.db.PackageStatus.built, True)
    bpo_test.assert_package("hello-world-wrapper", status="built")
    assert(not os.path.exists(wip_path + "/hello-world-1-r3.apk"))
    assert(os.path.exists(wip_path + "/hello-world-wrapper-1-r2.apk"))

    # Remove broken apk
    apk_path = final_path + "/hello-world-1-r4.apk"
    monkeypatch.setattr(bpo.repo.status, "is_apk_broken", bpo_test.true)
    assert os.path.exists(apk_path) is True
    func(arch, branch, final_path, bpo.db.PackageStatus.published)
    assert os.path.exists(apk_path) is False


def test_fix_db_vs_disk_existing_apks(monkeypatch):
    """ Test all code paths of bpo.repo.status.fix_db_vs_disk(), with existing
        apks in the final/wip repos."""
    arch = "x86_64"
    branch = "master"
    testdata = bpo.config.const.top_dir + "/test/testdata/"
    session = bpo.db.session()
    func = bpo.repo.status.fix_db_vs_disk

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    # Put hello-world-wrapper apk in wip repo, set to built
    wip_path = bpo.repo.wip.get_path(arch, branch)
    os.makedirs(wip_path)
    shutil.copy(testdata + "/hello-world-wrapper-1-r2.apk", wip_path)
    package = bpo.db.get_package(session, "hello-world-wrapper", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)

    # Put hello-world-wrapper apk in final repo, set to published
    final_path = bpo.repo.final.get_path(arch, branch)
    os.makedirs(final_path)
    shutil.copy(testdata + "/hello-world-1-r4.apk", final_path)
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.published)

    # Apks are present now -> no status change
    func(arch, branch)
    bpo_test.assert_package("hello-world-wrapper", status="built")
    bpo_test.assert_package("hello-world", status="published")


def test_fix_db_vs_disk_missing_apks(monkeypatch):
    """ Test all code paths of bpo.repo.status.fix_db_vs_disk(), with missing
        apks in the final/wip repos."""
    arch = "x86_64"
    branch = "master"
    session = bpo.db.session()
    func = bpo.repo.status.fix_db_vs_disk

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    # Everything is queued without existing apks -> no status change
    func(arch, branch)
    bpo_test.assert_package("hello-world", status="queued")
    bpo_test.assert_package("hello-world-wrapper", status="queued")

    # hello-world: published but missing apk -> status reset to queued
    package = bpo.db.get_package(session, "hello-world", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.published)
    func(arch, branch)
    bpo_test.assert_package("hello-world", status="queued")

    # hello-world-wrapper: built but missing apk -> status reset to queued
    package = bpo.db.get_package(session, "hello-world-wrapper", arch, branch)
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.built)
    func(arch, branch)
    bpo_test.assert_package("hello-world", status="queued")
