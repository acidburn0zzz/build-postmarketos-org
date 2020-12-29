# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import logging
import os

from flask import request
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.images
import bpo.ui

blueprint = bpo.api.blueprint


def get_files(request):
    """ Get all attached files and verify their names. """
    pattern = bpo.config.const.images.pattern_file
    ret = request.files.getlist("file[]")

    for img in ret:
        if not pattern.match(img.filename) or img.filename == "readme.html":
            raise ValueError(f"Invalid filename: {img.filename}")

    return ret


def get_image(session, branch, device, ui):
    ret = bpo.db.get_image(session, branch, device, ui)
    if not ret:
        raise ValueError(f"No unfinished image found with: device={device},"
                         " branch={branch}, ui={ui}")
    if ret.status != bpo.db.ImageStatus.building:
        raise RuntimeError(f"Image {ret} has unexpected status {ret.status}"
                           " instead of 'building'")
    return ret


def get_dir_name(request):
    pattern = bpo.config.const.images.pattern_dir
    ret = bpo.api.get_header(request, "Version")
    if not pattern.match(ret):
        raise ValueError(f"Invalid dir_name (X-BPO-Version): {ret}")
    return ret


@blueprint.route("/api/job-callback/build-image", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_build_image():
    branch = bpo.api.get_branch(request)
    device = bpo.api.get_header(request, "Device")
    dir_name = get_dir_name(request)
    job_id = bpo.api.get_header(request, "Job-Id")
    ui = bpo.api.get_header(request, "Ui")

    session = bpo.db.session()
    image = get_image(session, branch, device, ui)
    files = get_files(request)

    # Create target dir
    path = bpo.images.path(branch, device, ui, dir_name)
    os.makedirs(path, exist_ok=True)

    # Fill target dir
    for img in files:
        path_img = os.path.join(path, img.filename)
        logging.info(f"Saving {path_img}")
        img.save(path_img)

    # Generate readme.html
    path_readme = os.path.join(path, "readme.html")
    bpo.ui.generate_image_readme(image, path_readme)

    # Update database (status, job_id, dir_name, date)
    bpo.db.set_image_status(session, image, bpo.db.ImageStatus.published,
                            job_id, dir_name, datetime.datetime.now())
    bpo.ui.log_image(image, "api_job_callback_build_image")

    # Remove old image
    bpo.images.remove_old()

    # Start next build job
    bpo.repo.build()
    return "image received, kthxbye"
