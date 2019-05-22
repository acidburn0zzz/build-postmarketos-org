# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import glob
import logging
import os
import sqlalchemy
import sys

import bpo.config.const
import bpo.config.args

_engine = None
_metadata = None

# Tables
log = None


def init_tables():
    from sqlalchemy import Table, Column, Integer, String, Text

    self = sys.modules[__name__]
    metadata = sqlalchemy.MetaData()
    self.log = Table("log", metadata,
                     Column("id", Integer, primary_key=True),
                     Column("datetime", String),
                     Column("action", String),
                     Column("details", Text),
                     Column("payload", Text))
    self.package = Table("package", metadata,
                         Column("aport", String(100)),
                         Column("arch", String(10)),
                         Column("component", String(30)),
                         Column("time_spent", Integer),
                         Column("times_built", Integer))
    self.depends = Table("depends", metadata,
                         Column("id", Integer, primary_key=True),
                         Column("package_id", Integer),
                         Column("depend_id", Integer))

    metadata.create_all(self._engine)
    self._metadata = metadata


def init():
    """ Initialize db """
    self = sys.modules[__name__]
    url = "sqlite:///" + bpo.config.args.db_path
    self._engine = sqlalchemy.create_engine(url)

    init_tables()
