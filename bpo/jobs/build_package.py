# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.helpers.queue
import bpo.helpers.job


def run(queue_entry):
    bpo.helpers.queue.set_status(queue_entry, "BUILDING")
    bpo.helpers.job.run("build_package", {
        "build": """
            echo "stub: build package"
        """,
        "upload": """
            echo "stub: upload"
        """,
    })
