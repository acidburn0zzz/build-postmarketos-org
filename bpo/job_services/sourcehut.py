# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Job service for builds.sr.ht, see: https://man.sr.ht/builds.sr.ht """

import logging
import requests
import shlex

import bpo.config.args
import bpo.config.tokens
import bpo.db
from bpo.job_services.base import JobService


def api_request(path, payload):
    url = "https://builds.sr.ht/api/" + path
    headers = {"Authorization": "token " + bpo.config.tokens.sourcehut}
    ret = requests.post(url, headers=headers, json=payload)
    logging.debug("sourcehut response: " + ret.text)
    if not ret.ok:
        raise RuntimeError("sourcehut API request failed: " + url)
    return ret


def get_manifest(name, tasks, branch):
    url_api = bpo.config.args.url_api
    url_repo_wip = bpo.config.args.url_repo_wip
    ret = """
        image: alpine/latest
        packages:
        - coreutils
        - py3-requests
        sources:
        - "https://gitlab.com/postmarketOS/pmaports.git/"
        - "https://gitlab.com/postmarketOS/pmbootstrap.git/"
        environment:
          BPO_JOB_ID: "$JOB_ID"
          BPO_TOKEN_FILE: "./token"
          BPO_API_HOST: """ + shlex.quote(url_api) + """
          BPO_JOB_NAME: """ + shlex.quote(name) + """
          BPO_WIP_REPO_URL: """ + shlex.quote(url_repo_wip) + """
          BPO_WIP_REPO_ARG: '-mp "$BPO_WIP_REPO_URL"'
        tasks:
        - bpo_setup: |
           yes "" | ./pmbootstrap/pmbootstrap.py --aports=$PWD/pmaports -q init
    """

    ret = bpo.helpers.job.remove_additional_indent(ret, 8)[:-1]

    # Add tasks
    for name, script in tasks.items():
        script_indented = "   " + script[:-1].replace("\n", "\n   ")
        ret += "\n- {}: |\n{}".format(name, script_indented)
    return ret


class SourcehutJobService(JobService):

    def run_job(self, name, tasks, branch="master"):
        note = "WIP testing new bpo run job code"
        manifest = get_manifest(name, tasks, branch)
        print(manifest)
        result = api_request("jobs", {"manifest": manifest,
                                      "note": note,
                                      "tags": [name],
                                      "execute": True,
                                      "secrets": True})
        job_id = result.json()["id"]
        logging.info("Job started: " + self.get_link(job_id))
        return job_id

    def get_status(self, job_id):
        # TODO: get status from sourcehut
        return bpo.db.PackageStatus.failed

    def get_link(self, job_id):
        user = bpo.config.args.sourcehut_user
        return ("https://builds.sr.ht/~" + user + "/job/" + str(job_id))

    def init(self):
        bpo.config.tokens.require("sourcehut")
