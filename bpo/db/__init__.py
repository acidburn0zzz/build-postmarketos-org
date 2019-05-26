# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Database code, using sqlalchemy ORM.
    Usage example:
        session = bpo.db.session()
        log_entry = bpo.db.Log(action="db_init", details="hello world")
        session.add(log_entry)
        session.commit() """

import glob
import logging
import os
import sys
import json

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

import bpo.config.args


base = sqlalchemy.ext.declarative.declarative_base()
session = None


class Push(base):
    __tablename__ = "push"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)


class Commit(base):
    __tablename__ = "commit"
    id = Column(Integer, primary_key=True)
    ref = Column(String)
    message = Column(String)
    push_id = Column(Integer, ForeignKey("push.id"))


class Package(base):
    __tablename__ = "package"
    id = Column(Integer, primary_key=True)
    pkgname = Column(String)
    version = Column(String)
    repo = Column(String)


class PackageDependency(base):
    __tablename__ = "package_dependency"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer)
    dependency_id = Column(Integer)


class Queue(base):
    __tablename__ = "queue"
    id = Column(Integer, primary_key=True)
    # TODO


class Log(base):
    __tablename__ = "log"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    action = Column(Text)
    payload = Column(Text)
    push_id = Column(Integer, ForeignKey("push.id"))


    def __init__(self, action, payload=None, push=None):
        self.action = action
        self.payload = json.dumps(payload, indent=4) if payload else None
        self.push = push


def init_relationships():
    self = sys.modules[__name__]

    # log - n:1 - push
    self.Log.push = relationship("Push", back_populates="logs")
    self.Push.logs = relationship("Log", order_by=self.Log.id,
                                  back_populates="push")

    # commits - n:1 - push
    self.Commit.push = relationship("Push", back_populates="commits")
    self.Push.commits = relationship("Commit", order_by=self.Commit.id,
                                     back_populates="push")


def init():
    """ Initialize db """
    # Open DB and initialize
    self = sys.modules[__name__]
    url = "sqlite:///" + bpo.config.args.db_path
    engine = sqlalchemy.create_engine(url)
    init_relationships()
    self.base.metadata.create_all(engine)
    self.session = sqlalchemy.orm.sessionmaker(bind=engine)

    # Create log entry
    msg = Log(action="db_init")
    session = self.session()
    session.add(msg)
    session.commit()
