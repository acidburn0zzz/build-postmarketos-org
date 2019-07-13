# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import sys

from flask import Flask
import bpo.api.push_hook
import bpo.api.job_callback
import bpo.config.args
import bpo.config.tokens
import bpo.db


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def main():
    # Initialize logging, config, database
    logging_init()
    bpo.config.args.init()
    bpo.config.tokens.init()
    bpo.db.init()

    # Initialize flask server
    app = Flask(__name__)
    app.register_blueprint(bpo.api.push_hook.blueprint)
    app.register_blueprint(bpo.api.job_callback.blueprint)
    app.run(host=bpo.config.args.host, port=bpo.config.args.port)


if __name__ == "__main__":
    sys.exit(main())
