# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import sys

from flask import Flask
from bpo.helpers import config
import bpo.db
from bpo.api.gitlab import gitlab
from bpo.api.callback import callbacks


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def main():
    # Initialize logging, args, database
    logging_init()
    config.init()
    db.init()
    app = Flask(__name__)
    app.register_blueprint(gitlab)
    app.register_blueprint(callbacks)
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    sys.exit(main())
