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
import bpo.repo
import bpo.repo.tools
import bpo.repo.wip
import bpo.ui


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def auto_get_repo_missing():
    for branch in bpo.config.const.branches:
        for arch in bpo.config.const.architectures:
            bpo.jobs.get_repo_missing.run(arch, branch)


def main(return_app=False):
    """ :param return_app: return the flask app, instead of running it. This
                           is used in the testsuite. """
    # Initialize logging, config, database, repo tools/keys
    logging_init()
    bpo.config.args.init()
    bpo.config.tokens.init()
    bpo.db.init()
    bpo.repo.tools.init()
    bpo.repo.wip.do_keygen()

    # Initialize UI and update it with a new log message
    bpo.ui.init()
    bpo.ui.log_and_update("restart")

    # Kick off build jobs for queued packages
    bpo.repo.build()

    # Fill up queue with packages to build
    if bpo.config.args.auto_get_repo_missing:
        auto_get_repo_missing()

    # Initialize flask server
    app = Flask(__name__)
    app.register_blueprint(bpo.api.blueprint)
    if return_app:
        return app
    app.run(host=bpo.config.args.host, port=bpo.config.args.port,
            threaded=False)


if __name__ == "__main__":
    sys.exit(main())
