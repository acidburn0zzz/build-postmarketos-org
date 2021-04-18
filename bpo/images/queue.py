# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import threading
import logging

import bpo.db
import bpo.images.config
import bpo.repo

timer = None
timer_cond = threading.Condition()


def remove_not_in_config():
    """ Remove entries from the image table, which are not in published state
        and are no longer mentioned in the config. """
    session = bpo.db.session()
    result = session.query(bpo.db.Image).\
        filter(bpo.db.Image.status != bpo.db.ImageStatus.published).\
        all()

    for image in result:
        branch_config = bpo.images.config.get_branch_config(image.device,
                                                            image.branch)
        if branch_config and image.ui in branch_config["ui"]:
            continue

        bpo.ui.log_image(image, "image_removed_from_config")
        session.delete(image)
        session.commit()


def fill(now=None):
    """ Add new entries to the image table, based on
        bpo/config/const/images.py.
        :param now: current time, can be overwritten for tests """
    logging.info("Running bpo.images.queue.fill()")
    session = bpo.db.session()

    for img_cfg in bpo.images.config.get_images(now):
        branch = img_cfg["branch"]
        device = img_cfg["device"]
        ui = img_cfg["ui"]
        start = img_cfg["date-start"]

        # Skip if image is already being processed
        if bpo.db.get_image(session, branch, device, ui):
            continue

        # Skip if image was built already
        if session.query(bpo.db.Image).\
                filter_by(device=device,
                          branch=branch,
                          ui=ui,
                          status=bpo.db.ImageStatus.published).\
                filter(bpo.db.Image.date >= start).\
                all():
            continue

        # Add to queue
        img_db = bpo.db.Image(device, branch, ui)
        session.merge(img_db)
        session.commit()
        bpo.ui.log("add_image_to_queue", device=device, branch=branch, ui=ui)


def timer_stop():
    global timer
    global timer_cond

    with timer_cond:
        if not timer:
            return

        # If the thread is not running, cancel it
        timer.cancel()

        # If it is running, wait until finished
        timer.join()

        timer = None


def timer_iterate(next_interval=3600, repo_build=True):
    """ Run fill() and schedule a timer to do it again.

        All functions called in this thread need to be thread safe, or else we
        have bugs like #79!

        :param next_interval: when to check again (in seconds, gets passed to
                              the next iteration)
        :param repo_build: set to False to skip running bpo.repo.build() after
                           filling the queue (does *not* get passed to the next
                           iteration) """
    global timer
    global timer_cond

    fill()

    if repo_build:
        bpo.repo.build(no_repo_update=True)

    if not timer_cond.acquire(False):
        # timer_stop() is running
        return

    timer = threading.Timer(next_interval, timer_iterate, [next_interval])
    timer.daemon = True
    timer.name = "ImageTimerThread"
    timer.start()

    timer_cond.release()
