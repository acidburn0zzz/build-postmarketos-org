# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/jobs/build_package.py """
import bpo_test  # noqa
import bpo.config.const
import bpo.jobs.build_package


def test_do_build_strict(monkeypatch):
    monkeypatch.setattr(bpo.config.const, "no_build_strict", ["gcc*-*"])
    func = bpo.jobs.build_package.do_build_strict

    assert(func("gcc-armhf") is False)
    assert(func("gcc4-aarch64") is False)
    assert(func("gcc6-armv7") is False)

    assert(func("gcc") is True)
    assert(func("hello-world") is True)
