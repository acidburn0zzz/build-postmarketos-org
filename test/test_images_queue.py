# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Test bpo/images/queue.py """
import datetime
import time
import bpo_test  # noqa
import bpo.config.args
import bpo.config.const.images
import bpo.images.queue


def test_remove_not_in_config(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "qemu-amd64": {
                            "branches": ["master"],
                            "branch_configs": {
                                "master": {"ui": ["sxmo"]}
                                }
                        }})

    # Init and clear DB
    monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
    bpo_test.BPOServer()
    session = bpo.db.session()

    # 1. queued, does exist in config
    device = "qemu-amd64"
    branch = "master"
    ui = "sxmo"
    image = bpo.db.Image(device, branch, ui)
    session.merge(image)

    # 2. queued, does not exist in config
    ui = "unknown-ui-2"
    image = bpo.db.Image(device, branch, ui)
    session.merge(image)

    # 3. published, does not exist in config
    ui = "unknown-ui-3"
    image = bpo.db.Image(device, branch, ui)
    image.dir_name = "test-3"
    image.status = bpo.db.ImageStatus.published
    session.merge(image)

    # Commit and verify
    session.commit()
    bpo_test.assert_image(device, branch, "sxmo")
    bpo_test.assert_image(device, branch, "unknown-ui-2")
    bpo_test.assert_image(device, branch, "unknown-ui-3")

    # Delete entries and verify
    bpo.images.queue.remove_not_in_config()
    session = bpo.db.session()
    bpo_test.assert_image(device, branch, "sxmo")
    bpo_test.assert_image(device, branch, "unknown-ui-2", count=0)
    bpo_test.assert_image(device, branch, "unknown-ui-3")


def test_fill(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "qemu-amd64": {
                            "branches": ["master"],
                            "branch_configs": {
                                "master": {"date-start": "2021-01-01",
                                           "date-interval": 7,
                                           "ui": ["first",
                                                  "second",
                                                  "third",
                                                  "fourth"]}
                                }
                        }})
    date_now = datetime.datetime.fromisoformat("2021-01-10")
    date_within_interval = datetime.datetime.fromisoformat("2021-01-08")
    date_before_interval = datetime.datetime.fromisoformat("2021-01-07")
    device = "qemu-amd64"
    branch = "master"

    # Init and clear DB
    monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
    bpo_test.BPOServer()
    session = bpo.db.session()

    # 1. Image with status queued
    image = bpo.db.Image(device, branch, "first")
    image.date = date_within_interval
    session.merge(image)

    # 2. Image with status finished within the interval
    image = bpo.db.Image(device, branch, "second")
    image.date = date_within_interval
    image.dir_name = "test-2"
    image.status = bpo.db.ImageStatus.published
    session.merge(image)

    # 3. Image with status finished before the interval
    image = bpo.db.Image(device, branch, "third")
    image.date = date_before_interval
    image.dir_name = "test-3"
    image.status = bpo.db.ImageStatus.published
    session.merge(image)

    # Commit and verify
    session.commit()
    bpo_test.assert_image(device, branch, "first", count=1)
    bpo_test.assert_image(device, branch, "second", count=1)
    bpo_test.assert_image(device, branch, "third", count=1)
    bpo_test.assert_image(device, branch, "fourth", count=0)

    # Fill queue and verify again
    bpo.images.queue.fill(date_now)
    bpo_test.assert_image(device, branch, "first", count=1)
    bpo_test.assert_image(device, branch, "second", count=1)
    bpo_test.assert_image(device, branch, "third", count=2)
    bpo_test.assert_image(device, branch, "fourth", count=1)


def test_timer(monkeypatch):
    global fake_fill_i
    fake_fill_i = 0

    def fake_fill():
        global fake_fill_i
        fake_fill_i += 1
        print(f"fake_fill_i: {fake_fill_i}")

    # Clear the database
    monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
    bpo_test.BPOServer()

    # Run timer_iterate with a tiny interval
    monkeypatch.setattr(bpo.repo, "build", bpo_test.nop)
    monkeypatch.setattr(bpo.images.queue, "fill", fake_fill)
    bpo.images.queue.timer_iterate(0.01, False)

    # Let it run bpo.images.queue.fill() three times
    while fake_fill_i != 3:
        time.sleep(0.01)

    bpo.images.queue.timer_stop()
