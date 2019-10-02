# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import jinja2
import os
import bpo.config.const
import bpo.config.args
import bpo.db

env = None


def update():
    """ Update html_out/index.html """
    global env
    template = env.get_template("index.html")
    html = template.render(pkgcount_all=100)
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
