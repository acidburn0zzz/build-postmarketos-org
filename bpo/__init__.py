# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys

from flask import Flask
import bpo.api
import bpo.api.job_callback.build_package
import bpo.api.job_callback.get_repo_missing
import bpo.api.job_callback.sign_index
import bpo.api.push_hook.gitlab
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
    bpo.repo.tools.init()

    # Initialize flask server
    app = Flask(__name__)
    app.register_blueprint(bpo.api.blueprint)
    app.run(host=bpo.config.args.host, port=bpo.config.args.port)


if __name__ == "__main__":
    sys.exit(main())
