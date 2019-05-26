# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.helpers.job


def run(push_id):
    bpo.helpers.job.run("get_depends", {
        "hello": """
            echo "hello world"
            """,
        "pmbootstrap repo_missing": """
            # ./pmbootstrap.py repo_missing > repo_missing.json
            """,
        "submit": """
            # TODO: use push_id: """ + str(push_id) + """
            pmaports/.sr.ht/submit.py --json task-submit repo_missing.json
            """,
    })
