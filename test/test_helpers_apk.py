# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/helpers/apk.py """
import collections
import pytest

import bpo_test  # noqa
import bpo.helpers.apk


def test_apk_get_pkginfo_lines():
    with pytest.raises(RuntimeError) as e:
        bpo.helpers.apk.get_pkginfo_lines("/some/invalid/path")
        assert str(e.value).startswith("File does not exist")

    with pytest.raises(RuntimeError) as e:
        bpo.helpers.apk.get_pkginfo_lines(__file__)
        assert "is not a valid tar" in str(e.value)


def test_apk_get_metadata():
    apk = (bpo.config.const.top_dir +
           "/test/testdata/hello-world-wrapper-subpkg-1-r2.apk")

    expected = collections.OrderedDict()
    expected["pkgver"] = "1-r2"
    expected["origin"] = "hello-world-wrapper"

    assert bpo.helpers.apk.get_metadata(apk) == expected
