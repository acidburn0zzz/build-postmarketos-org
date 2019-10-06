# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Job service for builds.sr.ht, see: https://man.sr.ht/builds.sr.ht """

import logging
import requests
import yaml

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


def get_manifest(tasks):
    manifest = {"image": "alpine/latest",
                "packages": ["coreutils", "py3-requests"],
                "sources": ["https://gitlab.com/postmarketOS/pmaports.git/"],
                "environment": {},
                "secrets": []}
    ret = yaml.safe_dump(manifest)

    # Pyyaml's safe_dump chokes on ordereddicts, so format tasks manually. This
    # also makes sure that the formatting looks good, and is not in a single.
    ret += "tasks:\n"
    for name, script in tasks.items():
        script_indented = "   " + script.replace("\n", "\n   ")
        ret += "- {}: |\n{}".format(name, script_indented) + "\n"

    return ret


class SourcehutJobService(JobService):
    def script_setup(self, branch=None):
        # TODO: install pmbootstrap
        # TODO: yes "" | pmbootstrap init
        return """
            env
        """

    def run_job(self, name, tasks, branch=None):
        note = "WIP testing new bpo run job code"
        manifest = get_manifest(tasks)
        print(manifest)
        result = api_request("jobs", {"manifest": manifest,
                                      "note": note,
                                      "tags": [name],
                                      "execute": True,
                                      "secrets": True})
        job_id = result.json()["id"]
        logging.info("Job successfully started, got id: " + str(job_id))
        return job_id

    def get_status(self, job_id):
        # TODO: get status from sourcehut
        return bpo.db.PackageStatus.failed

    def get_link(self, job_id):
        user = bpo.config.args.sourcehut_user
        return ("https://builds.sr.ht/~" + user + "/job/" + str(job_id))

    def init(self):
        bpo.config.tokens.require("sourcehut")
