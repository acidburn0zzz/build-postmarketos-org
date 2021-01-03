# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later


class JobService:
    def init(self):
        """ Initialize the job service when the bpo server starts (make sure
            that tokens are there etc.) """
        pass

    def run_job(self, name, note, tasks):
        pass

    def get_link(self, job_id):
        pass
