# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Database code, using sqlalchemy ORM.
    Usage example:
        session = bpo.db.session()
        log = bpo.db.Log(action="db_init", details="hello world")
        session.add(log)
        session.commit() """

import glob
import logging
import os
import sys
import json

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, \
                       Table
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

    # commits.push_id - n:1 - push.id
    self.Commit.push = relationship("Push", back_populates="commits")
    self.Push.commits = relationship("Commit", order_by=self.Commit.id,
                                     back_populates="push")

    # log.push_id - n:1 - push.id
    self.Log.push = relationship("Push", back_populates="logs")
    self.Push.logs = relationship("Log", order_by=self.Log.id,
                                  back_populates="push")

    # package.depends - n:n - package.required_by
    # See "Self-Referential Many-to-Many Relationship" in:
    # https://docs.sqlalchemy.org/en/13/orm/join_conditions.html
    assoc = Table("package_dependency", base.metadata,
                  Column("package_id", ForeignKey("package.id"),
                         primary_key=True),
                  Column("dependency_id", ForeignKey("package.id"),
                         primary_key=True))
    self.Package.depends = relationship("Package", secondary=assoc,
        primaryjoin=self.Package.id==assoc.c.package_id,
        secondaryjoin=self.Package.id==assoc.c.dependency_id,
        order_by=self.Package.id,
        backref="required_by")


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
