# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Default values are stored in bpo/config/const/args.py. After
    bpo.config.args.init() ran, all values are available in bpo.config.args
    (e.g. bpo.config.args.job_service). """

import argparse
import sys
import bpo.config.const
import bpo.config.const.args


def job_service_local(parser):
    sub = parser.add_parser("local", help="run all jobs locally (debug)")

    sub.add_argument("--pmaports", dest="local_pmaports",
                     help="path to local pmaports.git checkout, the job will"
                          " run on a copy")
    sub.add_argument("--pmbootstrap", dest="local_pmbootstrap",
                     help="path to local pmbootstrap.git checkout, the job"
                          " will run on a copy")
    return sub


def job_service_sourcehut(parser):
    sub = parser.add_parser("sourcehut", help="run all jobs on sr.ht")

    sub.add_argument("-u", "--user", dest="sourcehut_user", help="username")
    return sub


def init():
    # Common arguments
    parser = argparse.ArgumentParser(description="postmarketOS build"
                                                 "coordinator", prog="bpo")
    parser.add_argument("-a", "--auto-get-depends", action="store_true",
                        help="automatically get missing packages (don't wait"
                             " for the push hook from gitlab)")
    parser.add_argument("-b", "--bind", dest="host",
                        help="host to listen on")
    parser.add_argument("-t", "--tokens",
                        help="path to tokens file, where hashes of generated"
                             " auth tokens are stored")
    parser.add_argument("-d", "--db-path", help="path to sqlite3 database")
    parser.add_argument("-m", "--mirror", help="the final repository location,"
                        " where published and properly signed packages can be"
                        " found")
    parser.add_argument("-f", "--force-final-repo-sign", action="store_true",
                        help="sign the final repo after starting the server,"
                             " even if it is incomplete. this is a workaround,"
                             " in case the final repo was signed with an"
                             " invalid key. it may lead to unexpected package"
                             " deletion. do not use.")
    parser.add_argument("-p", "--port", type=int, help="port to listen on")
    parser.add_argument("-r", "--repo-final-path",
                        help="where to create the final binary repository")
    parser.add_argument("-w", "--repo-wip-path",
                        help="apks remain in this WIP path, until a complete"
                             " pmaports.git push (of one or more commits) is"
                             " built, then all WIP apks are moved to the final"
                             " repo path")
    parser.add_argument("-i", "--images-path",
                        help="location of generated postmarketOS images")
    parser.add_argument("-o", "--html-out", help="directory, to which the html"
                        " status pages will be written while the bpo server"
                        " is running")
    parser.add_argument("--temp-path",
                        help="used for various things, like extracting"
                             " APKINDEX tools and for running local jobs (will"
                             " get wiped!)")
    parser.add_argument("--url-api", help="external URL to the bpo server for"
                        " accessing the API (ignored with local job service)")
    parser.add_argument("--url-repo-wip-http",
                        help="external URL to the WIP repo dir"
                             " (--repo-wip-path), HTTP protocol"
                             " (used for packages signed with WIP key)")
    parser.add_argument("--url-repo-wip-https",
                        help="external URL to the WIP repo dir"
                             " (--repo-wip-path), HTTPS protocol"
                             " (used for downloading the unsigned index, job"
                             " sign_index)")
    parser.add_argument("--url-images",
                        help="external URL to the images dir")

    # Job service subparsers
    job_service = parser.add_subparsers(title="job service",
                                        dest="job_service")
    job_service.required = True
    subparsers = [job_service_local(job_service),
                  job_service_sourcehut(job_service)]

    # Set defaults from module attributes
    for subparser in [parser] + subparsers:
        for action in subparser._actions:
            if action.dest == "help" or not action.help:
                continue
            default = getattr(bpo.config.const.args, action.dest)
            action.default = default
            action.help += " (default: {})".format(default)

    # Store result as module attributs (bpo.config.args.job_service etc.)
    args = parser.parse_args()
    self = sys.modules[__name__]
    for arg in vars(args):
        setattr(self, arg, getattr(args, arg))
