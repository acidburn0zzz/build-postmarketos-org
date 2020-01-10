# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Make the testsuite test itself. """
import pytest

import bpo_test
import bpo_test.trigger
import bpo.repo


def test_assert_package(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends()

    # Everything OK
    pkgname = "hello-world"
    func = bpo_test.assert_package
    func(pkgname, status="queued", version="1-r4")
    func(pkgname, status="queued")
    func(pkgname, version="1-r4")
    func("invalid-pkgname", exists=False)

    # Package not in db
    with pytest.raises(RuntimeError) as e:
        bpo_test.assert_package("invalid-pkgname")
        assert str(e.value).startswith("Expected package to exist in db")

    # Different status
    with pytest.raises(RuntimeError) as e:
        bpo_test.assert_package(pkgname, status="built")
        assert str(e.value).startswith("Expected status")

    # Different version
    with pytest.raises(RuntimeError) as e:
        bpo_test.assert_package(pkgname, version="1-r5")
        assert str(e.value).startswith("Expected version")

    # Package should not exist, but does
    with pytest.raises(RuntimeError) as e:
        bpo_test.assert_package(pkgname, exists=False)
        assert str(e.value).startswith("Package should NOT exist")
