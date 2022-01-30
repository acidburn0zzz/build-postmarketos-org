# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Make the testsuite test itself. """
import os
import pytest

import bpo_test
import bpo_test.const
import bpo_test.trigger
import bpo.repo


@pytest.mark.timeout(10)
def test_assert_package(monkeypatch):
    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    # Everything OK
    pkgname = "hello-world"
    func = bpo_test.assert_package
    func(pkgname, status="queued", version="1-r4")
    func(pkgname, status="queued")
    func(pkgname, version="1-r4")
    func("invalid-pkgname", exists=False)

    # Package not in db
    with pytest.raises(RuntimeError) as e:
        func("invalid-pkgname")
        assert str(e.value).startswith("Expected package to exist in db")

    # Different status
    with pytest.raises(RuntimeError) as e:
        func(pkgname, status="built")
        assert str(e.value).startswith("Expected status")

    # Different version
    with pytest.raises(RuntimeError) as e:
        func(pkgname, version="1-r5")
        assert str(e.value).startswith("Expected version")

    # Package should not exist, but does
    with pytest.raises(RuntimeError) as e:
        func(pkgname, exists=False)
        assert str(e.value).startswith("Package should NOT exist")


def test_const_pmaports_versions():
    """ Verify that bpo_test.const.version_* matches pmaports """
    pmaports_dir = bpo.config.const.top_dir + "/../pmbootstrap/aports"
    if not os.path.isdir(pmaports_dir):
        raise RuntimeError("Can't find pmaports, expected them here: '{}'"
                           " (if you want to add a way to override it, feel"
                           " free to submit a patch, see #45)"
                           .format(pmaports_dir))
    v_hello = bpo_test.const.version_hello_world
    v_wrapper = bpo_test.const.version_hello_world_wrapper
    pkgnames_versions = {"hello-world": v_hello,
                         "hello-world-wrapper": v_wrapper}
    for pkgname, version in pkgnames_versions.items():
        pkgver, pkgrel = version.split("-r")

        # Check APKBUILD for pkgver, pkgrel
        apkbuild_path = "{}/main/{}/APKBUILD".format(pmaports_dir, pkgname)
        with open(apkbuild_path, "r") as handle:
            apkbuild = handle.read()
            for match in ["pkgver=" + pkgver, "pkgrel=" + pkgrel]:
                if "\n" + match + "\n" in apkbuild:
                    continue
                raise RuntimeError("Can't find '{}' line in '{}'. You probably"
                                   " need to adjust the version_* vars in"
                                   " test/bpo_test/const.py."
                                   .format(match, apkbuild_path))
