# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests

import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


def test_callback_repo_missing_to_nop(monkeypatch):
    with bpo_test.BPOServer():
        # Trigger push-hook/gitlab (to create a Push entry with ID 1 in the DB)
        monkeypatch.setattr(bpo.jobs.get_repo_missing, "run", bpo_test.nop)
        bpo_test.trigger.push_hook_gitlab()

        # Trigger job-callback/get-repo-missing
        monkeypatch.setattr(bpo.repo, "build", bpo_test.nop)
        bpo_test.trigger.job_callback_get_repo_missing()


# FIXME: test all kinds of errors, e.g. invalid push id
