# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Full migration libraries like alembic are overkill for this simple program.
    Instead of creating a dedicated script for migrating back and forth with
    each change, only add three lines for each change below, and add a comment
    in bpo/db/__init__.py to the original db layout to indicate what has
    changed. This means we can only migrate forward, but that's fine for our
    use case. Whenever a new database file is created, it starts with the
    layout 0 defined in bpo/db/__init__.py and then applies all upgrades from
    here. """

import logging
import bpo.db


def version_get():
    result = bpo.db.engine.execute("PRAGMA user_version")
    version = [row[0] for row in result][0]
    return version


def version_set(version):
    bpo.db.engine.execute("PRAGMA user_version=" + str(version))
    logging.info("Database layout upgraded to v" + str(version))


def upgrade():
    engine = bpo.db.engine

    # Package: add index "arch-branch"
    if version_get() == 0:
        engine.execute("CREATE INDEX 'arch-branch'"
                       "ON 'package' (`arch`, `branch`)")
        version_set(1)

    # Log: add column "commit"
    if version_get() == 1:
        engine.execute("ALTER TABLE 'log' ADD COLUMN 'commit' VARCHAR")
        version_set(2)

    # Package: add index "status"
    if version_get() == 2:
        engine.execute("CREATE INDEX 'status'"
                       "ON 'package' (`status`)")
        version_set(3)

    # Package: add column "retry_count"
    if version_get() == 3:
        engine.execute("ALTER TABLE 'package'"
                       " ADD COLUMN 'retry_count'"
                       " INT DEFAULT(0)")
        version_set(4)
