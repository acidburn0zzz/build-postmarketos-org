# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from flask import request
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.repo.symlink
import bpo.repo.final
import bpo.ui

blueprint = bpo.api.blueprint


def save_apkindex(request):
    # Sanity checks
    files = request.files.getlist("file[]")
    if len(files) != 1:
        raise RuntimeError("Unexpected amount of uploaded files!")
    name = files[0].filename
    if name != "APKINDEX.tar.gz":
        raise RuntimeError("Unexpected file name: " + name)

    # Save to symlink repo
    branch = bpo.api.get_branch(request)
    arch = bpo.api.get_arch(request, branch)
    path = bpo.repo.symlink.get_path(arch, branch) + "/APKINDEX.tar.gz"
    logging.info("Saving " + path)
    files[0].save(path)


@blueprint.route("/api/job-callback/sign-index", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_sign_index():
    branch = bpo.api.get_branch(request)
    arch = bpo.api.get_arch(request, branch)

    # FIXME: check if the index signing was expected
    save_apkindex(request)

    bpo.ui.log("api_job_callback_sign_index", arch=arch, branch=branch)

    bpo.repo.final.update_from_symlink_repo(arch, branch)
    bpo.repo.wip.clean(arch, branch)
    bpo.repo.final.publish(arch, branch)

    return "alright, rollin' out the new repo"
