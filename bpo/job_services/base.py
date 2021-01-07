# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import enum


class JobStatus(enum.Enum):
    pending = 0
    queued = 1
    running = 2
    success = 3
    failed = 4


class JobService:
    def init(self):
        """ Initialize the job service when the bpo server starts (make sure
            that tokens are there etc.) """
        pass

    def run_job(self, name, note, tasks):
        pass

    def get_link(self, job_id):
        pass

    def get_status(self, job_id_check):
        """ :returns: JobStatus """
        return JobStatus.failed
