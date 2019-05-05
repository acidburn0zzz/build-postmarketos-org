# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import bpo.helpers.config
import bpo.helpers.queue
import bpo.jobs.build_package
import bpo.jobs.sign_index


def build(args):
    for arch in bpo.helpers.config.build_device_architectures:
        queue_entry = bpo.helpers.queue.get_entry_next(args, arch)
        if queue_entry:
            bpo.jobs.build_package.run(args, queue_entry)
        else:
            logging.info("bpo.helpers.repo.build(): everything has been built"
                         " already!")


def is_staging_repo_complete(args, arch):
    logging.info("STUB: bpo.helpers.repo.is_staging_repo_complete")
    return True


def index(args, arch):
    logging.info("STUB: bpo.helpers.repo.index")

    # TODO:
    # * rebuild APKINDEX locally
    # * update database

    if is_staging_repo_complete(args, arch):
        bpo.jobs.sign_index.run(args, arch)


def publish(args, arch):
    logging.info("STUB: bpo.helpers.repo.publish")

    # TODO:
    # * run rsync to publish the repo
    # * better do it in a retry-loop, in case it fails
    # * update database
