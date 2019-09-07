# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import shlex
import subprocess

import bpo.config.args
from bpo.job_services.base import JobService


class LocalJobService(JobService):
    def script_setup(self):
        """ Setup temp_path with copy of pmaports.git and symlink to
            pmbootstrap and remove locally built packages. """
        pmaports = shlex.quote(bpo.config.args.local_pmaports)
        pmbootstrap = shlex.quote(bpo.config.args.local_pmbootstrap)
        return """
            cp -r """ + pmaports + """ .
            ln -s """ + pmbootstrap + """ ./pmbootstrap.py
            echo "5tJ7sPJQ4fLSf0JoS81KSpUwoGMmbWk5Km0OJiAHWF2PM2cO7i" > ./token
            ./pmbootstrap.py -q -y zap -p
        """

    def run_print(self, command):
        print("% " + " ".join(command))
        subprocess.run(command, check=True)

    def run_job(self, name, tasks):
        host = shlex.quote("http://" + bpo.config.args.host +
                           ":" + str(bpo.config.args.port))
        env_vars = """
            export BPO_TOKEN_FILE="./token"
            export BPO_API_HOST=""" + host + """
        """

        # Create temp_path, where we can run the scripts
        temp_path = bpo.config.args.temp_path + "/local_job"
        if os.path.exists(temp_path):
            self.run_print(["sudo", "rm", "-rf", temp_path])
        self.run_print(["mkdir", "-p", temp_path])

        # Write each task's script into a temp file and run it
        temp_script = temp_path + "/.current_task.sh"
        for task, script in tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(temp_path) + "\n" +
                             env_vars + "\n" +
                             script)
            self.run_print(["sh", "-ex", temp_script])
