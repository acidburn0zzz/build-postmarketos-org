# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import shlex
import subprocess

import bpo.config.args
from bpo.job_services.base import JobService


class LocalJobService(JobService):
    def script_setup(self, branch=None):
        """ Setup temp_path with copy of pmaports.git/pmbootstrap.git and
            remove locally built packages.

            Optionally copy the WIP repository to the local packages dir, so we
            can build packages depending on others, without actually firing up
            a second webserver when testing locally and making the whole
            development / automated testing setup more complicated. When BPO is
            using a different backend than the local one (e.g. sourcehut), the
            WIP repository will not get copied over the local packages dir,
            instead it will get added as regular HTTPS mirror.

            :param branch: of the build package job, so we can copy the right
                           subdir of the WIP repository to the local packages
                           dir. """
        temp_path = bpo.config.args.temp_path + "/local_job"
        pmaports = bpo.config.args.local_pmaports
        pmbootstrap = bpo.config.args.local_pmbootstrap
        repo_wip_path = bpo.config.args.repo_wip_path
        uid = bpo.config.const.pmbootstrap_chroot_uid_user
        return """
            # Remove old temp dir
            temp_dir=""" + shlex.quote(temp_path) + """
            if [ -d "$temp_dir" ]; then
                sudo rm -rf "$temp_dir"
            fi

            # Prepare temp dir
            mkdir -p "$temp_dir"
            cd "$temp_dir"
            cp -r """ + shlex.quote(pmaports) + """ ./pmaports
            cp -r """ + shlex.quote(pmbootstrap) + """ ./pmbootstrap
            echo "5tJ7sPJQ4fLSf0JoS81KSpUwoGMmbWk5Km0OJiAHWF2PM2cO7i" > ./token
            ./pmbootstrap/pmbootstrap.py -q -y zap -p

            # Copy WIP repo
            branch=""" + shlex.quote(branch) + """
            work_path="$(./pmbootstrap/pmbootstrap.py -q config work)"
            packages_path="$work_path/packages"
            repo_wip_path=""" + shlex.quote(repo_wip_path) + """
            if [ -n "$branch" ] && [ -d "$repo_wip_path/$branch" ]; then
                sudo cp -r "$repo_wip_path/$branch" "$packages_path"
                sudo chown -R """ + shlex.quote(uid) + """ "$packages_path"
            fi
        """

    def run_print(self, command):
        print("% " + " ".join(command))
        subprocess.run(command, check=True)

    def run_job(self, name, tasks):
        # Create temp dir
        temp_path = bpo.config.args.temp_path + "/local_job"
        os.makedirs(temp_path, exist_ok=True)

        # Common env vars for each task
        host = ("http://" + bpo.config.args.host + ":" +
                str(bpo.config.args.port))
        wip_repo_path = bpo.config.args.repo_wip_path
        env_vars = """
            export BPO_TOKEN_FILE="./token"
            export BPO_API_HOST=""" + shlex.quote(host) + """
            export BPO_WIP_REPO_PATH=""" + shlex.quote(wip_repo_path) + """
            export BPO_WIP_REPO_URL="" # empty, because we copy it instead
            export BPO_WIP_REPO_ARG="" # empty, because we copy it instead
        """

        # Write each task's script into a temp file and run it
        temp_script = temp_path + "/current_task.sh"
        for task, script in tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(temp_path) + "\n" +
                             env_vars + "\n" +
                             script)
            self.run_print(["sh", "-ex", temp_script])
