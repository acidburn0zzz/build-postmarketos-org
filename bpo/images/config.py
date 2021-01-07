# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import datetime
import logging

import bpo.config.const.images


def get_device_branches(device):
    """ Get the branches, for which an image should be built for a certain
        device.
        :returns: list of branch names, e.g. ["master", "v20.05"] """
    images_cfg = bpo.config.const.images.images

    if device not in images_cfg:
        return []

    device_cfg = images_cfg[device]
    if "branches" in device_cfg:
        return device_cfg["branches"]

    return bpo.config.const.images.branches_default


def get_branch_config(device, branch):
    """ Combine the branch_config_default and images configs into a device and
        branch specific config.
        :returns: * None if device/branch was not found in the config
                  * the combined config, for example:
                    {"date-start": "2020-12-29",
                     "date-interval": "1 week",
                     "ui": ["phosh", "plasma-mobile", "i3wm"],
                     "installer": True,
                     "kernels": []} """
    if branch not in get_device_branches(device):
        logging.warning(f"images config: no entry for device={device},"
                        f"branch={branch}")
        return None

    ret = copy.copy(bpo.config.const.images.branch_config_default)

    device_cfg = bpo.config.const.images.images[device]
    if "branch_configs" in device_cfg:
        branch_configs = device_cfg["branch_configs"]
        # Overwrite default branch config with the one from "all" and with the
        # branch specific configuration
        for branch_key in ["all", branch]:
            if branch_key not in branch_configs:
                continue
            branch_cfg = branch_configs[branch_key]
            for key, value in branch_cfg.items():
                ret[key] = value

    return ret


def get_images(now=None):
    """ Generator that extracts one image from bpo/config/const/images.py at a
        time, so it can be added to the database if it does not exist yet.

        The yielded "date-start" is the same as in the config, but with
        "date-interval" (e.g. "1 week") added as often as possible, without
        having the date in the future.

        :param now: current time, can be overwritten for tests
        :yields: example: {"branch": "master",
                           "device": "pine64-pinephone",
                           "ui": "phosh",
                           "date-start": "2020-12-29",
                           "keep": 3} """
    if not now:
        now = datetime.datetime.now()

    for device in bpo.config.const.images.images:
        branches = get_device_branches(device)

        for branch in branches:
            branch_config = get_branch_config(device, branch)
            assert branch_config

            # Calculate start date
            start = datetime.datetime.strptime(branch_config["date-start"],
                                               "%Y-%m-%d")
            interval = datetime.timedelta(days=branch_config["date-interval"])
            while start + interval <= now:
                start += interval

            for ui in branch_config["ui"]:
                yield {"branch": branch,
                       "device": device,
                       "ui": ui,
                       "date-start": start,
                       "keep": branch_config["keep"]}
