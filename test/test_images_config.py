# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Test bpo/images/config.py """
import datetime
import bpo_test  # noqa
import bpo.config.const.images
import bpo.images.config


def test_get_device_branches(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "branches_default",
                        ["master"])
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "nokia-n900": {},
                        "qemu-amd64": {
                            "branches": ["master", "v20.05"]
                        }})

    func = bpo.images.config.get_device_branches
    assert func("invalid-device") == []
    assert func("qemu-amd64") == ["master", "v20.05"]
    assert func("nokia-n900") == ["master"]


def test_get_branch_config(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "qemu-amd64": {
                            "branches": ["master", "v20.05"],
                            "branch_configs": {
                                "all": {"keep": 5},
                                "master": {"keep": 10},
                            }
                        }})
    monkeypatch.setattr(bpo.config.const.images, "branch_config_default", {
                        "installer": False, "keep": 3})

    func = bpo.images.config.get_branch_config
    assert func("invalid-device", "invalid-branch") is None
    assert func("qemu-amd64", "invalid-branch") is None
    assert func("qemu-amd64", "master") == {"installer": False, "keep": 10}
    assert func("qemu-amd64", "v20.05") == {"installer": False, "keep": 5}


def test_get_images(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "qemu-amd64": {
                            "branches": ["master", "v20.05"],
                        }})
    monkeypatch.setattr(bpo.config.const.images, "branch_config_default", {
                        "date-interval": 7,
                        "date-start": "2021-01-05",
                        "ui": ["sxmo"],
                        "installer": False,
                        "keep": 3})

    # 14 days after date-start
    now = datetime.datetime.fromisoformat("2021-01-19")

    # 14 days fits the date-interval (7 days) twice
    date_expected = now

    # Let the generator run twice
    ret = list(bpo.images.config.get_images(now))
    assert ret == [{"branch": "master",
                    "device": "qemu-amd64",
                    "ui": "sxmo",
                    "date-start": date_expected,
                    "keep": 3},
                   {"branch": "v20.05",
                    "device": "qemu-amd64",
                    "ui": "sxmo",
                    "date-start": date_expected,
                    "keep": 3}]

    # Same result with 15 days after date-start, because it does not fit
    # date-interval tree times
    now = datetime.datetime.fromisoformat("2021-01-20")
    ret2 = list(bpo.images.config.get_images(now))
    assert ret2 == ret
