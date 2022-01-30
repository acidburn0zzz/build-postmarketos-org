# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/symlink.py """
import os
import pytest
import shutil

import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.repo.symlink


def test_repo_symlink_link_to_all_packages(monkeypatch):
    arch = "x86_64"
    branch = "master"
    wip_path = bpo.repo.wip.get_path(arch, branch)
    final_path = bpo.repo.final.get_path(arch, branch)
    symlink_path = bpo.repo.symlink.get_path(arch, branch)
    func = bpo.repo.symlink.link_to_all_packages

    path = bpo.config.const.top_dir + "/test/testdata/"
    apk_hello = path + "/hello-world-1-r4.apk"
    apk_hello_outdated = path + "/hello-world-1-r3.apk"
    apk_hello_wrapper = path + "/hello-world-wrapper-1-r2.apk"
    apk_hello_wrapper_subpkg = path + "/hello-world-wrapper-subpkg-1-r2.apk"

    expected_symlinks = ["hello-world-1-r4.apk",
                         "hello-world-wrapper-1-r2.apk",
                         "hello-world-wrapper-subpkg-1-r2.apk"]

    # Skip updating apkindex at the end of bpo.repo.clean()
    monkeypatch.setattr(bpo.repo.wip, "update_apkindex", bpo_test.nop)

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_depends("master")

    # 1. fail sanity check: packages don't exist in wip/final repo
    with pytest.raises(RuntimeError) as e:
        func(arch, branch)
        assert str(e.value).startswith("Found package in database, but not")

    # 2. Build repo with all in WIP repo
    os.makedirs(wip_path)
    shutil.copy(apk_hello, wip_path)
    shutil.copy(apk_hello_outdated, wip_path)
    shutil.copy(apk_hello_wrapper, wip_path)
    shutil.copy(apk_hello_wrapper_subpkg, wip_path)
    func(arch, branch)
    assert bpo.repo.get_apks(symlink_path) == expected_symlinks
    assert not os.path.exists(wip_path + "/" + apk_hello_outdated)

    # 3. Outdated apk in final repo, rest in WIP repo
    shutil.rmtree(symlink_path)
    os.makedirs(final_path)
    shutil.copy(apk_hello_outdated, final_path)
    func(arch, branch)
    assert bpo.repo.get_apks(symlink_path) == expected_symlinks

    # 4. Outdated apk and wrapper + subpkg in final repo, hello in WIP repo
    shutil.rmtree(symlink_path)
    shutil.rmtree(wip_path)
    os.makedirs(wip_path)
    shutil.copy(apk_hello, wip_path)
    shutil.copy(apk_hello_wrapper, final_path)
    shutil.copy(apk_hello_wrapper_subpkg, final_path)
    func(arch, branch)
    assert bpo.repo.get_apks(symlink_path) == expected_symlinks
