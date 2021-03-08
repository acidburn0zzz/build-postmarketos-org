# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo_test
import bpo_test.trigger
import bpo.jobs
import bpo.repo


def test_push_hook_gitlab_to_nop(monkeypatch):
    """ Pretend to be gitlab and send data to the push hook. Monkeypatch the
        get_depends job, so after successfully receiving the data, bpo
        won't try to actually get missing packages and build the repo. """

    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.jobs.get_depends, "run",
                            bpo_test.stop_server)
        bpo_test.trigger.push_hook_gitlab()
