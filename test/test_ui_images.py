# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/ui/images.py """
import os

import bpo_test  # noqa
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
