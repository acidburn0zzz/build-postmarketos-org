# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import jinja2
import os
from sqlalchemy import func

import bpo.config.const
import bpo.config.args
import bpo.db

env = None


def update():
    """ Update html_out/index.html """
    # Query information from DB
    session = bpo.db.session()
    log_entries = session.query(bpo.db.Log).order_by(bpo.db.Log.id.desc()
                    ).limit(50)
    pkgcount_all = session.query(func.count(bpo.db.Package.id)).scalar()
    pkgcount_queued = session.query(bpo.db.Package).filter_by(status=bpo.db.PackageStatus.waiting).count()
    pkgcount_failed = session.query(bpo.db.Package).filter_by(status=bpo.db.PackageStatus.failed).count()

    pkgs_building = session.query(bpo.db.Package).filter_by(status=bpo.db.PackageStatus.building)
    pkgs_failed = session.query(bpo.db.Package).filter_by(status=bpo.db.PackageStatus.failed)
    pkgs_queued = session.query(bpo.db.Package).filter_by(status=bpo.db.PackageStatus.waiting)

    # Fill template
    global env
    template = env.get_template("index.html")
    html = template.render(pkgcount_all=pkgcount_all,
                           pkgcount_queued=pkgcount_queued,
                           pkgcount_failed=pkgcount_failed,
                           log_entries=log_entries,
                           pkgs_building=pkgs_building,
                           pkgs_failed=pkgs_failed,
                           pkgs_queued=pkgs_queued)

    # Write to output dir
    output = bpo.config.args.html_out + "/index.html"
    output_temp = output + "_"
    with open(output_temp, "w") as handle:
        handle.write(html)
    os.rename(output_temp, output)


def init():
    global env
    loader = jinja2.PackageLoader("bpo", "../templates")
    autoescape = jinja2.select_autoescape(["html", "xml"])
    env = jinja2.Environment(loader=loader, autoescape=autoescape)

    os.makedirs(bpo.config.args.html_out, exist_ok=True)


def log_and_update(*args, **kwargs):
    """ Write one log message and update the output. Do this after making
        meaningful changes to the database, e.g. after a job callback was
        executed. See bpo.db.Log.__init__() for the list of parameters. """
    msg = bpo.db.Log(*args, **kwargs)
    session = bpo.db.session()
    session.add(msg)
    session.commit()

    update()
