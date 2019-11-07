# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo.api
import bpo.helpers.job

blueprint = bpo.api.blueprint


@blueprint.route("/api/public/update-job-status", methods=["POST"])
def public_update_job_status():
    bpo.helpers.job.update_package_status()
    return "done"
