# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import bpo.config.const
import bpo.helpers.queue
import bpo.jobs.build_package
import bpo.jobs.sign_index


def build():
    for arch in bpo.config.const.build_device_architectures:
        queue_entry = bpo.helpers.queue.get_entry_next(arch)
        if queue_entry:
            bpo.jobs.build_package.run(queue_entry)
        else:
            logging.info("bpo.helpers.repo.build(): everything has been built"
                         " already!")


def is_staging_repo_complete(arch):
    logging.info("STUB: bpo.helpers.repo.is_staging_repo_complete")
    return True


def index(arch):
    logging.info("STUB: bpo.helpers.repo.index")

    # TODO:
    # * rebuild APKINDEX locally
    # * update database

    if is_staging_repo_complete(arch):
        bpo.jobs.sign_index.run(arch)


def publish(arch):
    logging.info("STUB: bpo.helpers.repo.publish")

    # TODO:
    # * run rsync to publish the repo
    # * better do it in a retry-loop, in case it fails
    # * update database
