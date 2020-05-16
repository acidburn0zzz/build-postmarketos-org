# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys

from flask import Flask
import bpo.api
import bpo.api.job_callback.build_package
import bpo.api.job_callback.get_depends
import bpo.api.job_callback.sign_index
import bpo.api.public.update_job_status
import bpo.api.push_hook.gitlab
import bpo.config.args
import bpo.config.tokens
import bpo.db
import bpo.helpers.job
import bpo.repo
import bpo.repo.tools
import bpo.repo.wip
import bpo.ui


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def init_components():
    logging_init()
    bpo.config.args.init()
    bpo.config.tokens.init()
    bpo.db.init()
    bpo.repo.tools.init()
    bpo.repo.wip.do_keygen()
    bpo.helpers.job.init()
    bpo.ui.init()


def main(return_app=False):
    """ :param return_app: return the flask app, instead of running it. This
                           is used in the testsuite. """
    init_components()

    # Update UI by writing a new log message
    bpo.ui.log("restart")

    # Fix repo status inconsistencies (disk, db, job service)
    bpo.repo.status.fix()

    if bpo.config.args.force_final_repo_sign:
        # Force final repo sign
        logging.warning("WARNING: doing force final repo sign (-f)!")
        for branch, branch_data in bpo.config.const.branches.items():
            for arch in branch_data["arches"]:
                bpo.repo.symlink.create(arch, branch, True)
    else:
        # Kick off build jobs for queued packages
        bpo.repo.build()

    # Fill up queue with packages to build
    if bpo.config.args.auto_get_depends:
        for branch in bpo.config.const.branches.keys():
            bpo.jobs.get_depends.run(branch)

    # Restart is complete
    bpo.ui.log("restart_done")

    # Initialize flask server
    app = Flask(__name__)
    app.register_blueprint(bpo.api.blueprint)
    if return_app:
        return app
    app.run(host=bpo.config.args.host, port=bpo.config.args.port,
            threaded=False)


if __name__ == "__main__":
    sys.exit(main())
