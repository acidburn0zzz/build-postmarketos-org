# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/job_services/sourcehut.py """
import pytest
import sys

import bpo_test  # noqa
import bpo.db
import bpo.job_services.sourcehut


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
