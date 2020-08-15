# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Job service for builds.sr.ht, see: https://man.sr.ht/builds.sr.ht """

import logging
import requests
import shlex
import re

import bpo.config.args
import bpo.config.tokens
import bpo.db
from bpo.job_services.base import JobService


def api_request(path, payload=None, method="POST"):
    url = "https://builds.sr.ht/api/" + path
    headers = {"Authorization": "token " + bpo.config.tokens.sourcehut}
    ret = requests.request(method, url=url, headers=headers, json=payload)
    print("sourcehut response: " + ret.text)
    if not ret.ok:
        raise RuntimeError("sourcehut API request failed: " + url)
    return ret


def get_secrets_by_job_name(name):
    """ Have some privilege separation by only enabling the secrets, that are
        required for particular job types. In practice, this allows having the
        final repo sign key only available when necessary.
        :param name: job name (see bpo/jobs, e.g. "sign_index")
        :returns: string like "secrets:\n- first\n- second\n" """
    tokens = bpo.config.tokens
    secrets = [tokens.job_callback_secret]

    if name == "sign_index":
        secrets.append(tokens.final_sign_secret)

    ret = "secrets:\n"
    for secret in secrets:
        ret += "- " + str(secret) + "\n"
    return ret


def sanitize_task_name(name):
    """ Replace characters that are not allowed in sr.ht task names """
    name = name.lower()
    return re.sub(r'[^a-z0-9_\-]+', '_', name)


def get_manifest(name, tasks, branch):
    url_api = bpo.config.args.url_api
    url_repo_wip_http = bpo.config.args.url_repo_wip_http + "/"
    url_repo_wip_https = bpo.config.args.url_repo_wip_https + "/"
    ret = """
        image: alpine/latest
        packages:
        - coreutils
        - procps
        - py3-requests
        sources:
        - "https://gitlab.com/postmarketOS/pmaports.git/"
        - "https://gitlab.com/postmarketOS/pmbootstrap.git/"
        - "https://gitlab.com/postmarketOS/build.postmarketos.org.git/"
        environment:
          BPO_TOKEN_FILE: "/home/build/.token"
          BPO_API_HOST: """ + shlex.quote(url_api) + """
          BPO_JOB_NAME: """ + shlex.quote(name) + """
          BPO_WIP_REPO_URL: """ + shlex.quote(url_repo_wip_https) + """
          BPO_WIP_REPO_ARG: '-mp """ + shlex.quote(url_repo_wip_http) + """'
        """ + get_secrets_by_job_name(name) + """
        triggers:
        - action: webhook
          condition: failure
          url: """ + url_api + """/api/public/update-job-status
        tasks:
        - bpo_setup: |
           export BPO_JOB_ID="$JOB_ID"

           # Switch branch and release channel
           mkdir -p ~/.config
           ( echo "[pmbootstrap]"
             echo "is_default_channel = False" ) > ~/.config/pmbootstrap.cfg
           git -C pmaports checkout """ + shlex.quote(branch) + """

           yes "" | ./pmbootstrap/pmbootstrap.py --aports=$PWD/pmaports -q init
           sudo modprobe binfmt_misc
           sudo mount -t binfmt_misc none /proc/sys/fs/binfmt_misc

           branch="$(git -C pmaports rev-parse --abbrev-ref HEAD)"
           if [ "$branch" != """ + shlex.quote(branch) + """ ]; then
               echo "ERROR: pmbootstrap switched to the wrong branch: $branch"
               exit 1
           fi
    """

    ret = bpo.helpers.job.remove_additional_indent(ret, 8)[:-1]

    # Add tasks
    for name, script in tasks.items():
        script_indented = ("   export BPO_JOB_ID=\"$JOB_ID\"\n"
                           "   " + script[:-1].replace("\n", "\n   "))
        name = sanitize_task_name(name)
        ret += "\n- {}: |\n{}".format(name, script_indented)
    return ret


def convert_status(status):
    """ Convert sourchut status enum value to bpo.db.PackageStatus.
        Reference: https://man.sr.ht/builds.sr.ht/api.md#job-status-enum """
    if status in ["pending", "queued", "running"]:
        return bpo.db.PackageStatus.building
    if status == "success":
        return bpo.db.PackageStatus.built
    if status == "failed":
        return bpo.db.PackageStatus.failed

    # Fallback
    logging.critical("ERROR: can't convert sourcehut status: " + status)
    return bpo.db.PackageStatus.failed


class SourcehutJobService(JobService):

    def run_job(self, name, note, tasks, branch):
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
        result = api_request("jobs/" + str(job_id), method="GET")
        status = convert_status(result.json()["status"])
        logging.info("=> status: " + status.name)
        return status

    def get_link(self, job_id):
        user = bpo.config.args.sourcehut_user
        return ("https://builds.sr.ht/~" + user + "/job/" + str(job_id))

    def init(self):
        bpo.config.tokens.require("sourcehut")
        bpo.config.tokens.require("job_callback_secret")
        bpo.config.tokens.require("final_sign_secret")
