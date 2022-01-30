# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Test bpo/config/const/images.py """
import bpo_test  # noqa
import bpo.config.const.images


def test_branch_names():
    """ Branch names from the images config must be defined in
        pmb.config.const.branches. """
    cfg_branches = list(bpo.config.const.branches.keys())
    cfg_images = bpo.config.const.images.images

    for branch in bpo.config.const.images.branches_default:
        assert branch in cfg_branches

    for device in cfg_images:
        cfg_device = cfg_images[device]
        if "branches" in cfg_device:
            for branch in cfg_device["branches"]:
                assert branch in cfg_branches, \
                    f"{device}: invalid branch in 'branches'"
        if "branch_configs" in cfg_device:
            for branch in cfg_device["branch_configs"].keys():
                assert branch in ["all"] + cfg_branches, \
                    f"{device}: invalid branch in 'branch_configs'"


def test_ui():
    """ Verify that all UIs are in the allowlist, so we don't add an invalid
        one by accident and only notice it while trying to build it. """
    cfg_images = bpo.config.const.images.images
    cfg_default = bpo.config.const.images.branch_config_default
    allowlist = bpo.config.const.images.ui_allowlist

    assert "none" not in allowlist, "UI 'none' is intentionally not allowed," \
                                    " use 'console' instead"

    for ui in cfg_default["ui"]:
        assert ui in allowlist, f"branch_config_default: UI '{ui}' is not in" \
                " ui_allowlist. Typo, or needs to be added?"

    for device, image_config in cfg_images.items():
        if "branch_configs" not in image_config:
            continue
        for branch, branch_config in image_config["branch_configs"].items():
            if "ui" not in branch_config:
                continue
            for ui in branch_config["ui"]:
                assert ui in allowlist, f"{device}: {branch}: UI '{ui}' is" \
                    " not in ui_allowlist. Typo, or needs to be added?"


def test_config_keys():
    """ Test keys of various levels of the images config. """
    cfg_images = bpo.config.const.images.images
    cfg_default = bpo.config.const.images.branch_config_default
    cfg_default_keys = list(cfg_default.keys())

    for device in cfg_images:
        cfg_device = cfg_images[device]

        for key in cfg_device.keys():
            assert key in ["branches", "branch_configs"], \
                f"{device}: invalid key '{key}'"

        # All keys in the branch specific config must have a default value in
        # branch_config_default of the same type
        if "branch_configs" in cfg_device:
            for branch, branch_config in cfg_device["branch_configs"].items():
                for key in branch_config.keys():
                    assert key in cfg_default_keys, \
                        f"{device}: invalid key '{key}' in section '{branch}'"
                for key in branch_config.keys():
                    assert type(branch_config[key]) == type(cfg_default[key]),\
                        f"{device}: wrong type: '{key}' in section '{branch}'"\
                        # noqa (comparing types is fine here)

            continue
