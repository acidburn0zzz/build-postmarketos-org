# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import request
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.db
import bpo.ui

blueprint = bpo.api.blueprint


def get_package_by_job_id(session, job_id):
    result = session.query(bpo.db.Package).filter_by(job_id=job_id).all()
    if len(result):
        return result[0]

    raise RuntimeError("Unknown job id: " + job_id)


def job_callback_fail_continue_build_package():
    """ Own function, so it can easily be monkeypatched in the testsuite """
    bpo.repo.build()


@blueprint.route("/api/job-callback/fail", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_fail():
    job_name = bpo.api.get_header(request, "Job-Name")
    job_id = bpo.api.get_header(request, "Job-Id")

    if job_name == "build_package":
        # Get package
        session = bpo.db.session()
        package = get_package_by_job_id(session, job_id)

        # Change status to failed
        if package.status == bpo.db.PackageStatus.building:
            bpo.db.set_package_status(session, package,
                                      bpo.db.PackageStatus.failed)

        bpo.ui.log_package(package, "job_callback_fail_build_package")

        # build next package
        job_callback_fail_continue_build_package()
    else:
        # can't handle this failure
        bpo.ui.log("job_callback_fail_" + job_name, job_id=job_id)

    return "ouch, trying to recover..."
