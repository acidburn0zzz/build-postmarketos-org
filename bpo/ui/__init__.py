# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import jinja2
import os
from sqlalchemy import func

import bpo.config.const
import bpo.config.args
import bpo.db

env = None


def update_index(session, pkgs):
    """ Update html_out/index.html
        :param session: return value of bpo.db.session()
        :param pkgs: return value of bpo.db.get_all_packages_by_status() """
    # Query information from DB
    log_entries = session.query(bpo.db.Log).order_by(bpo.db.Log.id.desc()
                                                     ).limit(50)
    pkgcount = session.query(func.count(bpo.db.Package.id)).scalar()

    # Fill template
    global env
    template = env.get_template("index.html")
    html = template.render(bpo=bpo,
                           pkgcount=pkgcount,
                           pkgs=pkgs,
                           len=len,
                           log_entries=log_entries)

    # Write to output dir
    output = bpo.config.args.html_out + "/index.html"
    output_temp = output + "_"
    with open(output_temp, "w") as handle:
        handle.write(html)
    os.rename(output_temp, output)


def update(session):
    """ Update everything in html_out """
    pkgs = bpo.db.get_all_packages_by_status(session)
    update_index(session, pkgs)


def init():
    global env
    loader = jinja2.PackageLoader("bpo", "../data/templates")
    autoescape = jinja2.select_autoescape(["html", "xml"])
    env = jinja2.Environment(loader=loader, autoescape=autoescape)

    os.makedirs(bpo.config.args.html_out, exist_ok=True)


def log(*args, **kwargs):
    """ Write one log message and update the output. Do this after making
        meaningful changes to the database, e.g. after a job callback was
        executed. See bpo.db.Log.__init__() for the list of parameters.

        NOTE: Make sure that you have committed all changes to any open
              sessions (run session.commit() after doing changes), otherwise
              you will get a "database is locked" error. """
    msg = bpo.db.Log(*args, **kwargs)
    session = bpo.db.session()
    session.add(msg)
    session.commit()
    update(session)


def log_package(package, action):
    """ Convenience wrapper
        :param package: bpo.db.Package object """
    log(action=action, arch=package.arch, branch=package.branch,
        pkgname=package.pkgname, version=package.version,
        job_id=package.job_id)
