# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import shlex

import bpo.helpers.job


def run(push_id, arch):
    bpo.helpers.job.run("get_depends", {
        "pmbootstrap repo_missing": """
            ./pmbootstrap.py repo_missing > repo_missing.json
            """,
        "submit": """
            export BPO_API_ENDPOINT="get-repo-missing"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_PAYLOAD_FILES="repo_missing.json"
            export BPO_PAYLOAD_IS_JSON="1"
            export BPO_PUSH_ID=""" + shlex.quote(str(push_id)) + """

            pmaports/.sr.ht/submit.py
            """,
    })
