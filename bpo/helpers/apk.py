# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import os
import tarfile


def get_pkginfo_lines(apk):
    if not os.path.exists(apk):
        raise RuntimeError("File does not exist: " + apk)

    if not tarfile.is_tarfile(apk):
        raise RuntimeError("This apk is not a valid tar archive: " + apk)

    with tarfile.open(apk, "r:gz") as tar:
        with tar.extractfile(".PKGINFO") as handle:
            return handle.readlines()


def get_metadata(apk):
    """ :param apk: path to apk file
        :returns: dict with relevant metadata from .PKGINFO:
                  {"pkgver": "1-r3", "origin": "hello-world-meta"}
        NOTE: as shown in the example, pkgver is actually the full version
              ($pkgver-r$pkgrel)! """
    relevant_keys = ["origin", "pkgver"]

    ret = collections.OrderedDict()
    for line in get_pkginfo_lines(apk):
        line = line.decode()
        for key in relevant_keys:
            if not line.startswith(key + " = "):
                continue
            if key in ret:
                raise RuntimeError("key " + key + " found twice in .PKGINFO"
                                   " of apk file: " + apk)
            value = line[len(key + " = "):-1]
            ret[key] = value
    return ret
