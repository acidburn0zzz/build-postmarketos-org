# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/repo/wip.py """
import bpo_test
import bpo_test.trigger
import bpo.db
import bpo.repo
import bpo.repo.wip

import shutil
import os


def test_repo_wip_clean(monkeypatch):
    # *** Preparation ***
    arch = "x86_64"
    branch = "master"
    apk = "hello-world-wrapper-subpkg-1-r2.apk"
    apk_path = bpo.config.const.top_dir + "/test/testdata/" + apk
    wip_path = bpo.repo.wip.get_path(arch, branch)
    final_path = bpo.repo.final.get_path(arch, branch)
    func = bpo.repo.wip.clean

    # Fill the db with "hello-world", "hello-world-wrapper"
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
        bpo_test.trigger.job_callback_get_repo_missing()

    # Skip updating apkindex at the end of clean()
    monkeypatch.setattr(bpo.repo.wip, "update_apkindex", bpo_test.nop)

    # 1. apk is not in final repo, origin is in db => don't remove apk
    os.makedirs(wip_path)
    shutil.copy(apk_path, wip_path)
    func(arch, branch)
    assert bpo.repo.get_apks(arch, branch, wip_path) == [apk]

    # 2. apk is in final repo, origin is in db => remove apk
    os.makedirs(final_path)
    shutil.copy(apk_path, wip_path)
    shutil.copy(apk_path, final_path)
    func(arch, branch)
    assert bpo.repo.get_apks(arch, branch, wip_path) == []

    # Delete origin from db
    session = bpo.db.session()
    origin_pkgname = "hello-world-wrapper"
    package = bpo.db.get_package(session, origin_pkgname, arch, branch)
    session.delete(package)
    session.commit()
    assert bpo.db.get_package(session, origin_pkgname, arch, branch) is None

    # 3. apk is in final repo, origin is not in db => remove apk
    shutil.copy(apk_path, wip_path)
    func(arch, branch)
    assert bpo.repo.get_apks(arch, branch, wip_path) == []

    # 4. apk is not in final repo, origin is not in db => remove apk
    os.unlink(final_path + "/" + apk)
    shutil.copy(apk_path, wip_path)
    func(arch, branch)
    assert bpo.repo.get_apks(arch, branch, wip_path) == []
