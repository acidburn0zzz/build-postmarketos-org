# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Test bpo/images/__init__.py """
import datetime
import os
import sys
import bpo_test  # noqa
import bpo.config.args
import bpo.config.const.images
import bpo.images
import bpo.ui.dir


def test_pmos_ver():
    func = bpo.images.pmos_ver
    assert func("master") == "edge"
    assert func("v20.05") == "v20.05"


def test_path(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bpo", "-i", "/mnt/test", "local"])
    bpo.config.args.init()

    func = bpo.images.path
    assert func("master", "qemu-amd64", "sxmo", "20210105-1617") == \
        "/mnt/test/edge/qemu-amd64/sxmo/20210105-1617"


def test_remove_old(monkeypatch):
    monkeypatch.setattr(bpo.config.const.images, "images", {
                        "qemu-amd64": {
                            "branches": ["master"],
                            "branch_configs": {
                                "master": {"ui": ["sxmo"],
                                           "keep": 2}
                                }
                        }})
    branch = "master"
    device = "qemu-amd64"
    ui = "sxmo"

    # Init and clear DB
    monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)
    bpo_test.BPOServer()
    session = bpo.db.session()

    # Add four test images (similar to job_callback_build_image())
    for i in range(1, 5):
        date = datetime.datetime.fromisoformat(f"2021-01-0{i}")
        dir_name = f"2021010{i}-1337"

        # Add to DB
        image = bpo.db.Image(device, branch, ui)
        bpo.db.set_image_status(session, image, bpo.db.ImageStatus.published,
                                job_id=i, dir_name=dir_name, date=date)

        # Create dir with readme.html
        path_img = bpo.images.path_db_obj(image)
        os.makedirs(path_img)
        bpo.ui.dir.write_readme_image(f"{path_img}/readme.html", image)

    # Verify that image dirs were created
    dir_ui = f"{bpo.config.args.images_path}/edge/qemu-amd64/sxmo"
    assert os.path.exists(f"{dir_ui}/20210101-1337/readme.html")
    assert os.path.exists(f"{dir_ui}/20210102-1337/readme.html")
    assert os.path.exists(f"{dir_ui}/20210103-1337/readme.html")
    assert os.path.exists(f"{dir_ui}/20210104-1337/readme.html")

    # Run remove_old with keep=2
    bpo.images.remove_old()

    # Verify that the two oldest image dir were removed
    assert not os.path.exists(f"{dir_ui}/20210101-1337")
    assert not os.path.exists(f"{dir_ui}/20210102-1337")
    assert os.path.exists(f"{dir_ui}/20210103-1337/readme.html")
    assert os.path.exists(f"{dir_ui}/20210104-1337/readme.html")
