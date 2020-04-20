# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import shutil

import bpo_test
import bpo_test.trigger
import bpo.config.const
import bpo.repo.final
import bpo.jobs
import bpo.repo


def test_callback_depends_remove_deleted_packages_db(monkeypatch):
    # Stop bpo server after bpo.repo.build was called 3x
    global stop_count
    stop_count = 0

    def stop_count_increase(*args, **kwargs):
        global stop_count
        stop_count += 1
        print("stop_count_increase: " + str(stop_count))
        if stop_count == 3:
            bpo_test.stop_server()
    monkeypatch.setattr(bpo.repo, "build", stop_count_increase)

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        bpo_test.trigger.job_callback_get_depends("master")

        # Insert a new package, that does not exist in the depends payload
        session = bpo.db.session()
        arch = "x86_64"
        branch = "master"
        pkgname = "pkg-not-in-payload"
        version = "1337-r42"
        package_db = bpo.db.Package(arch, branch, pkgname, version)
        session.merge(package_db)
        session.commit()

        # Put fake apk with a valid name for the new db entry in final repo
        final_path = bpo.repo.final.get_path(arch, branch)
        apk_path = "{}/{}-{}.apk".format(final_path, pkgname, version)
        os.makedirs(final_path)
        shutil.copy(__file__, apk_path)

        # Indirectly trigger bpo.get_depends.remove_deleted_packages_db()
        bpo_test.trigger.job_callback_get_depends("master")

        # Package must not exist in db anymore (it isn't in the payload)
        # (apk still exists, because bpo.repo.build was monkeypatched)
        assert bpo.db.get_package(session, pkgname, arch, branch) is None


def test_callback_depends_update_package(monkeypatch):
    # Stop bpo server after bpo.repo.build was called 2x
    global stop_count
    stop_count = 0

    def stop_count_increase(*args, **kwargs):
        global stop_count
        stop_count += 1
        print("stop_count_increase: " + str(stop_count))
        if stop_count == 2:
            bpo_test.stop_server()
    monkeypatch.setattr(bpo.repo, "build", stop_count_increase)

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        bpo_test.trigger.job_callback_get_depends("master")

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
        bpo_test.trigger.job_callback_get_depends("master")
        bpo_test.assert_package(pkgname, status="queued", version="1-r4")


def test_callback_depends_to_nop(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger job-callback/get-depends
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")


# FIXME: test all kinds of errors, e.g. invalid push id
