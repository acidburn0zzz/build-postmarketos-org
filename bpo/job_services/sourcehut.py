# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Job service for builds.sr.ht, see: https://man.sr.ht/builds.sr.ht """

import logging
import os
import requests
import shlex
import yaml

import bpo.config.args
import bpo.config.tokens
import bpo.db
from bpo.job_services.base import JobService


def api_request(path, payload):
    url = "https://builds.sr.ht/api/" + path
    headers = {"Authorization": bpo.config.tokens.sourcehut}
    ret = requests.post(url, headers=headers, json=payload)
    logging.debug("sourcehut response: " + ret.text)
    if not ret.ok:
        raise RuntimeError("sourcehut API request failed: " + url)
    return ret


def get_manifest(tasks):
    manifest = {"image": "alpine/latest",
                "packages": ["coreutils", "py3-requests"],
                "sources": ["https://gitlab.com/postmarketOS/pmaports"],
                "environment": {},
                "secrets": [],
                "tasks": tasks}
    return yaml.dump(manifest)


class SourcehutJobService(JobService):
    def script_setup(self, branch=None):
        return """
            # TODO: install pmbootstrap
            # TODO: yes | pmbootstrap init
        """

    def run_job(self, name, tasks, branch=None):
        note = "WIP testing new bpo run job code"
        result = api_request("jobs", {"manifest": get_manifest(tasks),
                                     "note": note,
                                     "tags": [name],
                                     "execute": True,
                                     "secrets": True})
        # FIXME: extract job ID from result and return it
        return 0

    def get_status(self, job_id):
        # TODO: get status from sourcehut
        return bpo.db.PackageStatus.failed

    def get_link(self, job_id):
        user = bpo.config.args.sourcehut_user
        return ("https://builds.sr.ht/~" + user + "/job/" + str(job_id))

    def init(self):
        bpo.config.tokens.require("sourcehut")
