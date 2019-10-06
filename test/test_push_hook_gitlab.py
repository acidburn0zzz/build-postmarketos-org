# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


def test_push_hook_gitlab_to_nop(monkeypatch):
    """ Pretend to be gitlab and send data to the push hook. Monkeypatch the
        get_repo_missing job, so after successfully receiving the data, bpo
        won't try to actually get missing packages and build the repo. """

    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.jobs.get_repo_missing, "run", bpo_test.finish)
        bpo_test.trigger.push_hook_gitlab()


def test_push_hook_gitlab_to_repo_missing_to_nop(monkeypatch):
    """ Trigger the api push hook, then let bpo run the repo_missing job.
        Monkeypatch bpo.repo.build, so it stops after receiving repo_missing
        and does not try to build the repo. """
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.finish)
        bpo_test.trigger.push_hook_gitlab()


# FIXME: add test that provokes an error from server, e.g. by passing an
# invalid ref
