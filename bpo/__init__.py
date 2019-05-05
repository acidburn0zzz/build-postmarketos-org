# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import sys

from flask import Flask
import bpo.config.args as bpo_args
import bpo.config.tokens
import bpo.db as bpo_db
from bpo.api.gitlab import gitlab as bpo_gitlab
from bpo.api.callback import callbacks as bpo_callbacks


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def main():
    # Initialize logging, args, database
    logging_init()
    bpo_args.init()
    bpo_db.init()
    bpo.config.tokens.init()

    # Initialize flask server
    app = Flask(__name__)
    app.register_blueprint(bpo_gitlab)
    app.register_blueprint(bpo_callbacks)
    app.run(host=bpo_args.host, port=bpo_args.port)


if __name__ == "__main__":
    sys.exit(main())
