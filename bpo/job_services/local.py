# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import shlex
import subprocess

from bpo.helpers import config
from bpo.job_services.base import JobService


class LocalJobService(JobService):
    def script_setup(self):
        """ Setup tempdir with copy of pmaports.git and symlink to pmbootstrap. """
        pmaports = shlex.quote(config.local_pmaports)
        pmbootstrap = shlex.quote(config.local_pmbootstrap)
        return """
            cp -r """ + pmaports + """ .
            ln -s """ + pmbootstrap + """ ./pmbootstrap.py
        """

    def run_print(self, command):
        print("% " + " ".join(command))
        subprocess.run(command, check=True)

    def run_job(self, name, tasks):
        # Create tempdir, where we can run the scripts
        if os.path.exists(config.local_tempdir):
            self.run_print(["sudo", "rm", "-rf", config.local_tempdir])
        self.run_print(["mkdir", "-p", config.local_tempdir])

        # Write each task's script into a temp file and run it
        temp_script = config.local_tempdir + "/.current_task.sh"
        for task, script in tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(config.local_tempdir) + "\n" +
                             script)
            self.run_print(["sh", "-ex", temp_script])
