# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import glob
import logging
import os
import sqlite3

import bpo.helpers.constants
from bpo.helpers import config

_db = None


def get_version():
    """ Get the current version from the database if possible, or return 0. """
    cur = _db.db.cursor()
    ret = 0
    try:
        cur.execute("SELECT `version` FROM `db_version` WHERE 1")
        row = cur.fetchone()
        if row:
            ret = row[0]
    except sqlite3.OperationalError as e:
        pass
    return ret


def get_version_from_scheme(path):
    """ Get the version from a scheme file name (prefix digits). """
    return int(os.path.basename(path).split("-", 2)[0])


def update_version():
    """ Create or update the database scheme to the current one. """
    scheme_dir = bpo.helpers.constants.bpo_src + "/data/schemes"
    schemes = sorted(glob.glob(scheme_dir + "/*-*.sql"))

    # Check if update is needed
    highest = get_version_from_scheme(schemes[-1])
    current = get_version()
    if current == highest:
        return

    # Iteratively update database
    logging.debug("Updating database from version {} to {}".format(current,
                                                                   highest))
    for scheme in schemes:
        # Skip already applied schemes
        scheme_version = get_version_from_scheme(scheme)
        if scheme_version < current:
            continue

        # Apply scheme
        with open(scheme, "r", encoding="utf-8") as handle:
            sql = handle.read()
        _db.cursor().executescript(sql)
        _db.commit()

        # Sanity check
        current = get_version()
        if current != scheme_version:
            raise RuntimeError("Failed to upgrade database to {}, current"
                               " version is {}, this file is probably broken:"
                               " {}".format(scheme_version, current, scheme))


def insert_depends():
    logging.info("STUB: db: insert_depends")


def init():
    """ Initialize db """
    global _db
    _db = sqlite3.connect(config.database)

    # Iteratively build up database layout
    update_version()
