# Copyright 2019 Oliver Smith, Martijn Braam
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import logging
import sys
import os
import bpo.helpers.constants

tokens = os.path.realpath(bpo.helpers.constants.bpo_src + "/../.tokens.cfg")
host = "127.0.0.1"
port = 5000
db_path = "bpo.db"
gitlab_secret = None
job_service = "local"

local_pmaports = "../pmaports"
local_pmbootstrap = "../pmbootstrap/pmbootstrap.py"
local_tempdir = "_job_tmp"


def init():
    self = sys.modules[__name__]

    parser = argparse.ArgumentParser(description="postmarketOS build"
                                                 "coordinator", prog="bpo")
    parser.add_argument("-b", "--bind", default="127.0.0.1", dest="host",
                        help="host to listen on (default: 127.0.0.1)")
    parser.add_argument("-t", "--tokens", default=self.tokens,
                        help="path to tokens file, where hashes of generated"
                             " auth tokens are stored (default: " +
                             self.tokens + ")")
    parser.add_argument("-d", "--db-path", default=self.db_path,
                        help="path to sqlite3 database (default: " +
                             self.db_path + ")")
    parser.add_argument("-p", "--port", default=self.port, type=int,
                        help="port to listen on (default: " + str(self.port) +
                             ")")

    args = parser.parse_args()

    # FIXME: add job_service and job_service args again!

    for arg in vars(args):
        setattr(self, arg, getattr(args, arg))
