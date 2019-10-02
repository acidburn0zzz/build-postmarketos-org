# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

""" Database code, using sqlalchemy ORM.
    Usage example:
        session = bpo.db.session()
        log = bpo.db.Log(action="db_init", details="hello world")
        session.add(log)
        session.commit() """

import enum
import glob
import logging
import os
import sys
import json

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.sql
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, \
                       Table, Boolean, Index, Enum
from sqlalchemy.orm import relationship

import bpo.config.args


base = sqlalchemy.ext.declarative.declarative_base()
session = None
init_relationships_complete = False


class Push(base):
    __tablename__ = "push"
    id = Column(Integer, primary_key=True)
    branch = Column(String)
    date = Column(DateTime)


    def __init__(self, branch):
        # FIXME: set date to current date!
        self.branch = branch

class Commit(base):
    __tablename__ = "commit"
    id = Column(Integer, primary_key=True)
    ref = Column(String)
    message = Column(String)
    push_id = Column(Integer, ForeignKey("push.id"))


class PackageStatus(enum.Enum):
    waiting = 0
    building = 1
    built = 2
    published = 3


class Package(base):
    __tablename__ = "package"
    id = Column(Integer, primary_key=True)
    arch = Column(String)
    branch = Column(String)
    pkgname = Column(String)
    status = Column(Enum(PackageStatus))
    build_id = Column(Integer, unique=True)

    # The following columns represent the latest state. We don't store the
    # history in bpo (avoids complexity, we have the git history for that).
    version = Column(String)
    repo = Column(String)

    Index("pkgname-arch-branch", pkgname, arch, branch, unique=True)

    # Package.depends: see init_relationships() below.


    def __str__(self):
        depends=[]
        for depend in self.depends:
            depends.append(depend.pkgname)
        return (self.arch + "/" + self.repo + "/" + self.pkgname + "-" +
                self.version + "@" + self.branch + " (pmOS depends: " +
                str(depends) + ")")


    def __init__(self, arch, branch, pkgname, version):
        self.arch = arch
        self.branch = branch
        self.pkgname = pkgname
        self.version = version
        self.status = PackageStatus.waiting


    def depends_built(self):
        for depend in self.depends:
            if depend.status.value < PackageStatus.built.value:
                return False
        return True


class Log(base):
    __tablename__ = "log"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True),
                           server_default=sqlalchemy.sql.func.now())
    action = Column(Text)
    details = Column(Text)
    payload = Column(Text)
    arch = Column(Text)
    branch = Column(Text)


    def __init__(self, action, details=None, payload=None, arch=None,
                 branch=None):
        self.action = action
        self.details = json.dumps(details, indent=4) if details else None
        self.payload = json.dumps(payload, indent=4) if payload else None
        self.arch = arch
        self.branch = branch


def init_relationships():
    # Only run this once!
    self = sys.modules[__name__]
    if self.init_relationships_complete:
        return
    self.init_relationships_complete = True

    # commits.push_id - n:1 - push.id
    self.Commit.push = relationship("Push", back_populates="commits")
    self.Push.commits = relationship("Commit", order_by=self.Commit.id,
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


def get_package(session, pkgname, arch, branch):
    result = session.query(bpo.db.Package).filter_by(arch=arch,
                                                     branch=branch,
                                                     pkgname=pkgname).all()
    return result[0] if len(result) else None
