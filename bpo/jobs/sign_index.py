# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo.helpers.job


def run(arch, branch):
    bpo.helpers.job.run("sign_index", {
        "sign": """
            echo "stub: sign stuff"
        """,
        "upload": """
            echo "stub: upload"
        """,
    })
