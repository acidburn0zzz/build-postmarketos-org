# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import glob
import importlib
import logging
import os

import bpo.helpers.config
import bpo.helpers.configfile
import bpo.db


def parse():
    """ Parse commandline arguments, sorted alphabetically. """
    default_config_path = os.path.realpath(bpo.helpers.config.bpo_src +
                                           "/../.bpo.cfg")

    parser = argparse.ArgumentParser(prog="bpo")
    parser.add_argument("-b", "--bind", default="127.0.0.1", dest="host",
                        help="host to listen on (default: 127.0.0.1)")
    parser.add_argument("-c", "--config", default=default_config_path,
                        help="path to config, where credentials are stored"
                             " etc. (default: " + default_config_path + ")")
    parser.add_argument("-d", "--db-path", default="bpo.db",
                        help="path to sqlite3 database (default: bpo.db)")
    parser.add_argument("-p", "--port", default=1338, type=int,
                        help="port to listen on (default: 1338)")

    # Job services (import each .py and add their parser)
    sub = parser.add_subparsers(title="job service", dest="job_service")
    sub.required = True
    for path in glob.glob(bpo.helpers.config.bpo_src + "/job_services/*.py"):
        name = os.path.splitext(os.path.basename(path))[0]
        module = "bpo.job_services." + name
        importlib.import_module(module).add_args_parser(sub)

    return parser.parse_args()


def args_api_init(args):
    """ Import api call scripts and store the reply functions in args:
        args.api = {"/api/push_hook/gitlab": bpo.api.push_hook.gitlab.reply(),
                    ...}

        This way we only need to import them once, and we have a safe whitelist
        of possible api-calls (not going the other way around of opening a file
        from the user-supplied path). """
    setattr(args, "api", {})
    for path in glob.glob(bpo.helpers.config.bpo_src + "/api/*/*.py"):
        # Get dirname and filename without extension
        dirname = os.path.basename(os.path.dirname(path))
        name = os.path.splitext(os.path.basename(path))[0]
        logging.debug("Setting up API call: " + dirname + "/" + name)

        # Put reply() in args.api["/api/$dirname/$name"]
        module = "bpo.api." + dirname + "." + name
        url_path = "/api/" + dirname + "/" + name
        args.api[url_path] = importlib.import_module(module).reply


def args_job_service_init(args):
    module = "bpo.job_services." + args.job_service
    setattr(args, "job_service_module", importlib.import_module(module))


def init():
    args = parse()

    # Extend args
    bpo.db.init(args) # args.db
    bpo.helpers.configfile.init(args) # args.token_push_hook_gitlab
    args_api_init(args) # args.api
    args_job_service_init(args) # args.job_service_run

    return args
