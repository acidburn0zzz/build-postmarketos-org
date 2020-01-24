# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/db/migrate.py """
import bpo_test  # noqa
import bpo.config.const
import bpo.jobs.build_package

import shutil


def test_upgrade_twice_from_v0(tmpdir, monkeypatch):
    # Copy bpo.layout0.db to tmpdir
    db0_temp = str(tmpdir) + "/bpo.db"
    db0_orig = (bpo.config.const.top_dir + "/test/testdata/bpo.layout0.db")
    shutil.copy(db0_orig, db0_temp)
    monkeypatch.setattr(bpo.config.args, "db_path", db0_temp)
    assert bpo.config.args.db_path == db0_temp

    # Verify upgrading to latest
    bpo.db.init()

    # Verify upgrading again (crashes if missing version_set())
    bpo.db.init()
