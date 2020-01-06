# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/job_services/sourcehut.py """
import pytest
import sys

import bpo_test  # noqa
import bpo.config.const
import bpo.config.tokens
import bpo.db
import bpo.job_services.sourcehut


# This test does not need access to sourcehut
def test_sourcehut_get_secrets_by_job(monkeypatch):
    # Initialize enough of bpo server, so get_job_service() works
    tokens_cfg = bpo.config.const.top_dir + "/test/test_tokens.cfg"
    monkeypatch.setattr(sys, "argv", ["bpo.py", "-t", tokens_cfg, "sourcehut"])
    bpo.init_components()

    func = bpo.job_services.sourcehut.get_secrets_by_job_name
    assert(func("any_job_name") == "secrets:\n- f00d\n")
    assert(func("sign_index") == "secrets:\n- f00d\n- c4f3\n")


@pytest.mark.sourcehut
def test_sourcehut_get_status(monkeypatch):
    # Initialize enough of bpo server, so get_job_service() works
    monkeypatch.setattr(sys, "argv", ["bpo.py", "sourcehut"])
    bpo.init_components()

    # Get the job service
    js = bpo.helpers.job.get_job_service()

    # https://builds.sr.ht/~ollieparanoid/job/94567
    assert(js.get_status(94567) == bpo.db.PackageStatus.failed)

    # https://builds.sr.ht/~ollieparanoid/job/94499
    assert(js.get_status(94499) == bpo.db.PackageStatus.built)
