# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.helpers.job


def run(arch):
    bpo.helpers.job.run("sign_index", {
        "sign": """
            echo "stub: sign stuff"
        """,
        "upload": """
            echo "stub: upload"
        """,
    })
