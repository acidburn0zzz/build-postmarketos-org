# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.helpers.job
import bpo.jobs
import bpo.repo
import bpo.ui


def test_push_hook_gitlab_to_nop(monkeypatch):
    """ Pretend to be gitlab and send data to the push hook. Monkeypatch the
        get_depends job, so after successfully receiving the data, bpo
        won't try to actually get missing packages and build the repo. """

    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.jobs.get_depends, "run",
                            bpo_test.stop_server)
        bpo_test.trigger.push_hook_gitlab()


def test_push_hook_gitlab_get_pkgnames_commits():
    payload = {"object_kind": "push",
               "ref": "refs/heads/master",
               "checkout_sha": "deadbeef",
               "commits":
               [{"id": "1337f00",
                 "message": "main/postmarketos-ui-phosh: clean-up\n",
                 "timestamp": "2019-05-25T16:23:30Z",
                 "url": "https://gitlab.com/...d91164de15fd209af628b42",
                 "author": {"name": "John Doe", "email": "john@localhost"},
                 "added": ["device/main/device-pine64-pinephone/APKBUILD",
                           "main/hello-world/APKBUILD",
                           "random/other/file",
                           "/APKBUILD"],
                 "modified": ["main/postmarketos-ui-phosh/APKBUILD"],
                 "removed": ["temp/ofono/APKBUILD"]}]}

    ret = bpo.api.push_hook.gitlab.get_pkgnames_commits(payload)
    assert ret == {"device-pine64-pinephone": "1337f00",
                   "hello-world": "1337f00",
                   "postmarketos-ui-phosh": "1337f00",
                   "ofono": "1337f00"}


def test_push_hook_gitlab_reset_to_queued(monkeypatch):
    """ Have two failed packages, hello-world and hello-world-wrapper, and
        test if both get successfully reset to queued because
        main/hello-world/APKBUILD was modified in the pushed commit. """

    with bpo_test.BPOServer():
        # Fill the db with "hello-world", "hello-world-wrapper"
        monkeypatch.setattr(bpo.helpers.job, "update_status", bpo_test.nop)
        monkeypatch.setattr(bpo.repo, "build", bpo_test.nop)
        bpo_test.trigger.job_callback_get_depends("master")

        # Set both packages to failed
        session = bpo.db.session()
        for pkgname in ["hello-world", "hello-world-wrapper"]:
            package = bpo.db.get_package(session, pkgname, "x86_64", "master")
            package.status = bpo.db.PackageStatus.failed
            package.retry_count = 2
            session.merge(package)
            session.commit()
            bpo.ui.log_package(package, "job_update_package_status_failed")
        print("DEBUG9")

        bpo_test.assert_package("hello-world", status="failed", retry_count=2)
        bpo_test.assert_package("hello-world-wrapper", status="failed",
                                retry_count=2)

        # Run the gitlab push hook where hello-world was modified
        monkeypatch.setattr(bpo.jobs.get_depends, "run",
                            bpo_test.stop_server)
        bpo_test.trigger.push_hook_gitlab()

    # Verify status reset
    bpo_test.assert_package("hello-world", status="queued", retry_count=0)
    bpo_test.assert_package("hello-world-wrapper", status="queued",
                            retry_count=0)
