# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo.config.const
import bpo_test
import os
import requests
import sys

# Add test dir to import path (so we can import bpo_test)
topdir = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/.."))
sys.path.insert(0, topdir)


def api_request(path, headers, payload=None, files=None):
    """ Send one HTTP request to the bpo server's API and stop the test if the
        request fails. """
    ret = requests.post("http://127.0.0.1:5000/api/" + path, headers=headers,
                        json=payload, files=files)
    if not ret.ok:
        bpo_test.stop_server_nok()


def push_hook_gitlab():
    token = bpo.config.const.test_tokens["push_hook_gitlab"]
    headers = {"X-Gitlab-Token": token}
    payload = {"object_kind": "push",
               "ref": "refs/heads/master",
               "checkout_sha": "deadbeef",
               "commits":
               [{"id": "5e9e102a00e58541ed91164de15fd209af628b42",
                 "message": "main/postmarketos-ui-phosh: clean-up\n",
                 "timestamp": "2019-05-25T16:23:30Z",
                 "url": "https://gitlab.com/...d91164de15fd209af628b42",
                 "author": {"name": "John Doe", "email": "john@localhost"},
                 "added": [],
                 "modified": ["main/postmarketos-ui-phosh/APKBUILD"],
                 "removed": []}]}
    api_request("push-hook/gitlab", headers, payload)


def job_callback_get_repo_missing():
    """ Note that the versions must match the current versions in pmaports.git,
        otherwise the bpo server will build the current packages and complain
        later on, that the version isn't matching. """
    token = bpo.config.const.test_tokens["job_callback"]
    headers = {"X-BPO-Job-Id": "1",
               "X-BPO-Token": token}

    # master/x86_64: "hello-world", "hello-world-wrapper"
    file_name = "repo_missing.master.x86_64.json"
    file_path = (bpo.config.const.top_dir + "/test/testdata/" + file_name)
    files = [("file[]", (file_name, open(file_path, "rb"),
                         "application/octet-stream"))]

    # Other branches and arches: no packages (simplifies tests)
    file_path = bpo.config.const.top_dir + "/test/testdata/empty_list.json"
    for branch in bpo.config.const.branches:
        for arch in bpo.config.const.architectures:
            if branch == "master" and arch == "x86_64":
                continue
            file_name = "repo_missing." + branch + "." + arch + ".json"
            files.append(("file[]", (file_name, open(file_path, "rb"),
                                     "application/octet-stream")))

    api_request("job-callback/get-repo-missing", headers, files=files)
