# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests

import bpo_test
import bpo.jobs
import bpo.repo


def trigger_push_hook_gitlab():
    token = "iptTdfRNwSvg8ycZqiEdNhMqGalvsgvSXp91SIk2dukG74BNVu"
    payload = {"object_kind":"push",
               "ref": "refs/heads/master",
               "checkout_sha": "deadbeef",
               "commits":
                [{"id": "5e9e102a00e58541ed91164de15fd209af628b42",
                  "message": "main/postmarketos-ui-phosh: clean-up\n",
                  "timestamp": "2019-05-25T16:23:30Z",
                  "url": "https:\/\/gitlab.com\/...d91164de15fd209af628b42",
                  "author": {"name": "John Doe", "email": "john@localhost"},
                  "added": [],
                  "modified": ["main/postmarketos-ui-phosh/APKBUILD"],
                  "removed": []}]}
    ret = requests.post("http://127.0.0.1:5000/api/push-hook/gitlab",
                  json=payload, headers={"X-Gitlab-Token": token})
    assert(ret)


def test_push_hook_gitlab_to_nop(monkeypatch):
    """ Pretend to be gitlab and send data to the push hook. Monkeypatch the
        get_repo_missing job, so after successfully receiving the data, bpo
        won't try to actually get missing packages and build the repo. """

    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.jobs.get_repo_missing, "run", bpo_test.nop)
        trigger_push_hook_gitlab()


def test_push_hook_gitlab_to_repo_missing_to_nop(monkeypatch):
    """ Trigger the api push hook, then let bpo run the repo_missing job.
        Monkeypatch bpo.repo.build, so it stops after receiving repo_missing
        and does not try to build the repo. """
    with bpo_test.BPOServer():
        monkeypatch.setattr(bpo.repo, "build", bpo_test.nop)
        trigger_push_hook_gitlab()



# FIXME: add test that provokes an error from server, e.g. by passing an
# invalid ref
