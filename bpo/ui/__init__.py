# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import jinja2
import os
import logging
import shutil
from sqlalchemy import func

import bpo.config.const
import bpo.config.args
import bpo.db

env = None


def update_badge(session, pkgs):
    """ Update html_out/badge.svg
        :param session: return value of bpo.db.session()
        :param pkgs: return value of bpo.db.get_all_packages_by_status() """
    # Get new name
    new = "up-to-date"
    if pkgs["failed"].count():
        new = "failed"
    elif pkgs["building"].count() or pkgs["queued"].count():
        new = "building"

    # Copy to output dir
    source = bpo.config.const.top_dir + "/data/badges/" + new + ".svg"
    target = bpo.config.args.html_out + "/badge.svg"
    target_temp = target + "_"
    shutil.copy(source, target_temp)
    os.rename(target_temp, target)


def log_entries_by_day(session):
    """ :returns: {"2019-01-01": [a, b, ...],
                   "2019-01-02": [c, d, ...], ... }
                   a, b, c, d: bpo.db.Log objects """
    entries = session.query(bpo.db.Log).order_by(bpo.db.Log.id.desc()
                                                 ).limit(50)
    ret = collections.OrderedDict()
    for entry in entries:
        day = entry.date.strftime("%Y-%m-%d")
        if day not in ret:
            ret[day] = []
        ret[day].append(entry)
    return ret


def update_index(session, pkgs):
    """ Update html_out/index.html
        :param session: return value of bpo.db.session()
        :param pkgs: return value of bpo.db.get_all_packages_by_status() """
    # Query information from DB
    log_entries_days = log_entries_by_day(session)
    pkgcount = session.query(func.count(bpo.db.Package.id)).scalar()

    # Fill template
    global env
    template = env.get_template("index.html")
    html = template.render(bpo=bpo,
                           pkgcount=pkgcount,
                           pkgs=pkgs,
                           len=len,
                           log_entries_days=log_entries_days)

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
    update_badge(session, pkgs)


def copy_static():
    """ Copy the static dir to _html_out, as much in an atomic operation as
        possible. """
    source = bpo.config.const.top_dir + "/data/static"
    target = bpo.config.args.html_out + "/static"
    temp = target + "_"

    logging.info("Copying " + source + " to " + target)

    if os.path.exists(temp):
        shutil.rmtree(temp)

    shutil.copytree(source, temp)

    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.move(temp, target)


def init():
    global env
    loader = jinja2.PackageLoader("bpo", "../data/templates")
    autoescape = jinja2.select_autoescape(["html", "xml"])
    env = jinja2.Environment(loader=loader, autoescape=autoescape)

    os.makedirs(bpo.config.args.html_out, exist_ok=True)
    copy_static()


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
