# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import logging
import sys
import os
import bpo.config.const

tokens = bpo.config.const.top_dir + "/.tokens.cfg"
host = "127.0.0.1"
port = 5000
db_path = "bpo.db"
gitlab_secret = None
job_service = "local"
mirror = "http://postmarketos.brixit.nl/postmarketos"
temp_path = bpo.config.const.top_dir + "/_temp"
repo_path = bpo.config.const.top_dir + "/_repo"
repo_wip_path = bpo.config.const.top_dir + "/_repo_wip"

local_pmaports = os.path.realpath(bpo.config.const.top_dir +
                                  "/../pmbootstrap/aports")
local_pmbootstrap = os.path.realpath(bpo.config.const.top_dir +
                                     "/../pmbootstrap")


def job_service_local(parser):
    sub = parser.add_parser("local", help="run all jobs locally (debug)")

    sub.add_argument("--pmaports", dest="local_pmaports",
                     help="path to local pmaports.git checkout, the job will"
                          " run on a copy")
    sub.add_argument("--pmbootstrap", dest="local_pmbootstrap",
                     help="path to local pmbootstrap.git checkout, the job"
                          " will run on a copy")
    return sub


def init():
    # Common arguments
    parser = argparse.ArgumentParser(description="postmarketOS build"
                                                 "coordinator", prog="bpo")
    parser.add_argument("-b", "--bind", dest="host",
                        help="host to listen on")
    parser.add_argument("-t", "--tokens",
                        help="path to tokens file, where hashes of generated"
                             " auth tokens are stored")
    parser.add_argument("-d", "--db-path", help="path to sqlite3 database")
    parser.add_argument("-m", "--mirror", help="the final repository location,"
                        " where published and properly signed packages can be"
                        " found")
    parser.add_argument("-p", "--port", type=int, help="port to listen on")
    parser.add_argument("-r", "--repo-path",
                        help="where to create the final binary repository")
    parser.add_argument("-w", "--repo-wip-path",
                        help="apks remain in this WIP path, until a complete"
                             " pmaports.git push (of one or more commits) is"
                             " built, then all WIP apks are moved to the final"
                             " repo path")
    parser.add_argument("--temp-path",
                        help="used for various things, like extracting"
                             " APKINDEX tools and for running local jobs (will"
                             " wiped!)")

    # Job service subparsers
    job_service = parser.add_subparsers(title="job service",
                                        dest="job_service")
    job_service.required = True
    subparsers = [job_service_local(job_service)]

    # Set defaults from module attributes
    self = sys.modules[__name__]
    for subparser in [parser] + subparsers:
        for action in subparser._actions:
            if action.dest == "help" or not action.help:
                continue
            default = getattr(self, action.dest)
            action.default = default
            action.help += " (default: {})".format(default)

    # Overwrite module attributes with result
    args = parser.parse_args()
    for arg in vars(args):
        setattr(self, arg, getattr(args, arg))
