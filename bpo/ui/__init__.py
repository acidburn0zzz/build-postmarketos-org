# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import jinja2
import os
import logging
import shutil
import threading
from sqlalchemy import func

import bpo.config.const
import bpo.config.args
import bpo.db

env = None
ui_update_cond = threading.Condition()


def update_badge(session, pkgs, imgs):
    """ Update html_out/badge.svg
        :param session: return value of bpo.db.session()
        :param pkgs: return value of bpo.db.get_all_packages_by_status()
        :param imgs: return value of bpo.db.get_all_images_by_status()
        :returns: one of: "up-to-date", "failed", "building" """
    # Get new name
    new = "up-to-date"
    if bpo.db.get_failed_packages_count_relevant(session) \
            or imgs["failed"].count():
        new = "failed"
    elif pkgs["building"].count() \
            or imgs["building"].count() \
            or pkgs["queued"].count() \
            or imgs["queued"].count():
        new = "building"

    # Copy to output dir
    source = bpo.config.const.top_dir + "/data/badges/" + new + ".svg"
    target = bpo.config.args.html_out + "/badge.svg"
    target_temp = target + "_"
    shutil.copy(source, target_temp)
    os.rename(target_temp, target)

    return new


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


def commit_link(commit):
    short = commit[0:6]
    url = f"{bpo.config.const.commit_url}/{commit}"
    return f"<a href='{url}' class='commit'>{short}</a>"


def update_index(session, pkgs, imgs):
    """ Update html_out/index.html
        :param session: return value of bpo.db.session()
        :param pkgs: return value of bpo.db.get_all_packages_by_status()
        :param imgs: return value of bpo.db.get_all_images_by_status() """
    # Query information from DB
    log_entries_days = log_entries_by_day(session)
    pkgcount = session.query(func.count(bpo.db.Package.id)).scalar()
    imgcount = session.query(func.count(bpo.db.Image.id)).scalar()

    # Fill template
    global env
    template = env.get_template("index.html")
    html = template.render(bpo=bpo,
                           commit_link=commit_link,
                           pkgcount=pkgcount,
                           pkgs=pkgs,
                           imgcount=imgcount,
                           imgs=imgs,
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
    global ui_update_cond

    pkgs = bpo.db.get_all_packages_by_status(session)
    imgs = bpo.db.get_all_images_by_status(session)

    with ui_update_cond:
        update_index(session, pkgs, imgs)
        update_badge(session, pkgs, imgs)


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
    templates_dir = bpo.config.const.top_dir + "/data/templates"
    loader = jinja2.FileSystemLoader(templates_dir)
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


def log_package(package, action, depend_pkgname=None, commit=None):
    """ Convenience wrapper
        :param package: bpo.db.Package object """
    log(action=action, arch=package.arch, branch=package.branch,
        pkgname=package.pkgname, version=package.version,
        job_id=package.job_id, retry_count=package.retry_count,
        depend_pkgname=depend_pkgname, commit=commit)


def log_image(image, action):
    """ Convenience wrapper
        :param image: bpo.db.Image object """
    log(action=action,
        device=image.device,
        branch=image.branch,
        ui=image.ui,
        job_id=image.job_id,
        retry_count=image.retry_count,
        dir_name=image.dir_name)
