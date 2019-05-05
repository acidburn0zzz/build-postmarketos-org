# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import shlex
import subprocess

import bpo.config.args
from bpo.job_services.base import JobService


class LocalJobService(JobService):
    def script_setup(self):
        """ Setup tempdir with copy of pmaports.git and symlink to pmbootstrap. """
        pmaports = shlex.quote(bpo.config.args.local_pmaports)
        pmbootstrap = shlex.quote(bpo.config.args.local_pmbootstrap)
        return """
            cp -r """ + pmaports + """ .
            ln -s """ + pmbootstrap + """ ./pmbootstrap.py
        """

    def run_print(self, command):
        print("% " + " ".join(command))
        subprocess.run(command, check=True)

    def run_job(self, name, tasks):
        # Create tempdir, where we can run the scripts
        tempdir = bpo.config.args.local_tempdir
        if os.path.exists(tempdir):
            self.run_print(["sudo", "rm", "-rf", tempdir])
        self.run_print(["mkdir", "-p", tempdir])

        # Write each task's script into a temp file and run it
        temp_script = tempdir + "/.current_task.sh"
        for task, script in tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(tempdir) + "\n" +
                             script)
            self.run_print(["sh", "-ex", temp_script])
