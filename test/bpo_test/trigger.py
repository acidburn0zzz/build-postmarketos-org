# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import requests
import sys

# Add test dir to import path (so we can import bpo_test)
topdir = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/.."))
sys.path.insert(0, topdir)

import bpo_test


def api_request(path, headers, payload):
    """ Send one HTTP request to the bpo server's API and stop the test if the
        request fails. """
    ret = requests.post("http://127.0.0.1:5000/api/" + path, headers=headers,
                        json=payload)
    if not ret.ok:
        bpo_test.finish_nok()


def push_hook_gitlab():
    token = "iptTdfRNwSvg8ycZqiEdNhMqGalvsgvSXp91SIk2dukG74BNVu"
    headers = {"X-Gitlab-Token": token}
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
    api_request("push-hook/gitlab", headers, payload)


def job_callback_get_repo_missing():
    """ Note that the versions must match the current versions in pmaports.git,
        otherwise the bpo server will build the current packages and complain
        later on, that the version isn't matching. """
    token = "5tJ7sPJQ4fLSf0JoS81KSpUwoGMmbWk5Km0OJiAHWF2PM2cO7i"
    headers = {"X-BPO-Arch": "x86_64",
               "X-BPO-Branch": "master",
               "X-BPO-Token": token}
    payload = [{"pkgname": "hello-world",
                "repo": "main",
                "version": "1-r4",
                "depends": []},
               {"pkgname": "hello-world-wrapper",
                "repo": "main",
                "version": "1-r2",
                "depends": ["hello-world"]}]
    api_request("job-callback/get-repo-missing", headers, payload)
