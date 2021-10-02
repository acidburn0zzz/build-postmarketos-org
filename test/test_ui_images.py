# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/ui/images.py """
import glob
import json
import jsonschema
import os
import sys

import bpo_test  # noqa
import bpo.config.const.args
import bpo.ui.images


def test_get_file_size_human(monkeypatch):
    func = bpo.ui.images.get_file_size_human
    fake_size = 0
    path = "/invalid"

    def fake_getsize(path):
        return fake_size
    monkeypatch.setattr(os.path, "getsize", fake_getsize)

    fake_size = 1023
    assert func(path) == "1023 B"

    fake_size = 1024
    assert func(path) == "1.0 KiB"

    fake_size = 1536
    assert func(path) == "1.5 KiB"

    fake_size = 1024 * 1024 * 1.5
    assert func(path) == "1.5 MiB"

    fake_size = 1024 * 1024 * 1024 * 1.54321
    assert func(path) == "1.5 GiB"

    fake_size = 1024 * 1024 * 1024 * 1000 * 1.5
    assert func(path) == "1500.0 GiB"


def get_dict_by_val(dict_list, key, val):
    for d in dict_list:
        if key in d and d[key] == val:
            return d
    return None


def test_write_index_json(monkeypatch):

    def fake_iglob(path):
        for f in ["edge/nokia-n900/i3wm/20210101-0000/first.txt",
                  "edge/nokia-n900/i3wm/20210101-0000/first.txt.sha256",
                  "edge/nokia-n900/i3wm/20210101-0000/first.txt.sha512",
                  "edge/nokia-n900/i3wm/20210101-0000/index.html",
                  "edge/nokia-n900/i3wm/20210101-0000/second.txt",
                  "edge/nokia-n900/i3wm/20210101-0000/third.txt",
                  "edge/nokia-n900/i3wm/20210102-0000/first.txt",
                  "edge/nokia-n900/xfce4/20210102-0000/first.txt",
                  "edge/pine64-pinephone/sxmo/20210102-0000/first.txt",
                  "v21.06/pine64-pinephone/sxmo/20210102-0000/first.txt"]:
            yield f"{bpo.config.args.images_path}/{f}"
    monkeypatch.setattr(glob, "iglob", fake_iglob)

    def fake_getsize(path):
        return 1337
    monkeypatch.setattr(os.path, "getsize", fake_getsize)

    monkeypatch.setattr(sys, "argv", ["bpo", "local"])
    bpo.config.args.init()

    bpo.ui.images.write_index_json()

    with open("_images/index.json", "r") as handle:
        index = json.load(handle)
    with open("test/testdata/index.schema.json", "r") as handle:
        schema = json.load(handle)

    try:
        jsonschema.validate(index, schema)
    except jsonschema.exceptions.ValidationError as e:
        assert False, f"Failed to validate json against schema: {e}"

    with open("test/testdata/index.json.expected", "r") as handle:
        expected = json.load(handle)

    assert index == expected

    # edge/nokia-n900/i3wm/20210101-0000/third.txt
    version = get_dict_by_val(index["releases"], "name", "edge")
    assert version
    device = get_dict_by_val(version["devices"], "name", "nokia-n900")
    assert device
    ui = get_dict_by_val(device["interfaces"], "name", "i3wm")
    assert ui
    image = get_dict_by_val(ui["images"], "name", "third.txt")
    assert image
