# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import requests
import shlex

import bpo.config.args
import bpo.db
from bpo.job_services.base import JobService


class SourcehutJobService(JobService):
    def script_setup(self, branch=None):
        return """
            # TODO: install pmbootstrap
            # TODO: yes | pmbootstrap init
        """

    def run_job(self, name, tasks, branch=None):
       # TODO: send job to sourcehut and return the ID
       return 0

    def get_status(self, job_id):
        # TODO: get status from sourcehut
        return bpo.db.PackageStatus.failed

    def get_link(self, job_id):
        user = bpo.config.args.sourcehut_user
        return ("https://builds.sr.ht/~" + user + "/job/" + str(job_id))

    def init(self):
        bpo.config.tokens.require("sourcehut")
