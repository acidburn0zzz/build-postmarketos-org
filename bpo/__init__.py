# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys

from flask import Flask
import bpo.api
import bpo.api.job_callback.build_image
import bpo.api.job_callback.build_package
import bpo.api.job_callback.get_depends
import bpo.api.job_callback.sign_index
import bpo.api.public.update_job_status
import bpo.api.push_hook.gitlab
import bpo.config.args
import bpo.config.tokens
import bpo.db
import bpo.helpers.job
import bpo.images.queue
import bpo.repo
import bpo.repo.tools
import bpo.repo.wip
import bpo.ui
import bpo.ui.dir


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")


def init_components():
    logging_init()
    bpo.config.args.init()
    bpo.config.tokens.init()
    bpo.db.init()
    bpo.repo.tools.init()
    bpo.repo.wip.do_keygen()
    bpo.helpers.job.init()
    bpo.ui.init()


def main(return_app=False, fill_image_queue=True):
    """ :param return_app: return the flask app, instead of running it. This
                           is used in the testsuite.
        :param fill_image_queue: add new images (if the interval has been
                                 reached). This is disabled in tests, where we
                                 don't want to test building images. """
    init_components()

    # Update UI by writing a new log message
    bpo.ui.log("restart")

    # Maintenance tasks (fix repo inconsistencies, remove old images etc.)
    bpo.repo.status.fix()
    bpo.images.queue.remove_not_in_config()
    bpo.images.remove_old()
    bpo.ui.dir.write_all()

    if bpo.config.args.force_final_repo_sign:
        # Force final repo sign
        logging.warning("WARNING: doing force final repo sign (-f)!")
        for branch, branch_data in bpo.config.const.branches.items():
            for arch in branch_data["arches"]:
                bpo.repo.symlink.create(arch, branch, True)
    else:
        # Kick off build jobs for queued packages / images
        if fill_image_queue:
            bpo.images.queue.timer_iterate(repo_build=False)
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


def stop():
    """ Clean up after running the BPO Server. Used in the testsuite. """
    bpo.images.queue.timer_stop()


if __name__ == "__main__":
    sys.exit(main())
