# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import random
import requests
import shlex
import subprocess
import threading

import bpo.config.args
import bpo.db
from bpo.job_services.base import JobService


class LocalJobServiceThread(threading.Thread):
    """ Local jobs are running on the same machine, but in a different
        thread. """
    def __init__(self, name, tasks, branch):
        threading.Thread.__init__(self, name="job:" + name)
        self.name = name
        self.tasks = tasks
        self.branch = branch
        self.job_id = random.randint(1000000, 9999999)

        # Prepare log
        self.log_path = (bpo.config.args.temp_path + "/local_job_logs/" +
                         str(self.job_id) + ".txt")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        logging.info("Job " + name + " started, logging to: " + self.log_path)

    def run_print(self, command):
        with open(self.log_path, "a") as handle:
            handle.write("% " + " ".join(command))
            subprocess.run(command, check=True, stdout=handle, stderr=handle)

    def run_print_try(self, command):
        """ Try to execute a shell command, on failure send fail request to the
            server. """
        try:
            # Put this in an extra function, so we can easily monkeypatch
            # it in the testsuite
            self.run_print(command)
        except Exception as e:
            url = "http://{}:{}/api/job-callback/fail".format(
                    bpo.config.args.host, bpo.config.args.port)
            token = bpo.config.const.test_tokens["job_callback"]
            headers = {"X-BPO-Job-Name": self.name,
                       "X-BPO-Job-Id": str(self.job_id),
                       "X-BPO-Token": token}
            requests.post(url, headers=headers)
            raise

    def run(self):
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
            export BPO_JOB_ID=""" + str(self.job_id) + """
            export BPO_JOB_NAME=""" + shlex.quote(self.name) + """
            export BPO_WIP_REPO_PATH=""" + shlex.quote(wip_repo_path) + """
            export BPO_WIP_REPO_URL="" # empty, because we copy it instead
            export BPO_WIP_REPO_ARG="" # empty, because we copy it instead
        """

        # Write each task's script into a temp file and run it
        temp_script = temp_path + "/current_task.sh"
        for task, script in self.tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(temp_path) + "\n" +
                             env_vars + "\n" +
                             script)
            self.run_print_try(["sh", "-ex", temp_script])


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
        token = bpo.config.const.test_tokens["job_callback"]
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
            echo """ + shlex.quote(token) + """ > ./token
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

    def run_job(self, name, tasks, branch=None):
       thread = LocalJobServiceThread(name=name, tasks=tasks, branch=branch)
       thread.start()
       return thread.job_id

    def update_package_status_after_restart(self):
        """ Set all packages that were building to 'failed' after the local
            job service has been restarted, since this means ^C had been
            pressed."""
        building = bpo.db.PackageStatus.building
        failed = bpo.db.PackageStatus.failed

        session = bpo.db.session()
        result = session.query(bpo.db.Package).filter_by(status=building).all()
        for package in result:
            package.status = failed
            bpo.ui.log_and_update(action="job_service_local_restart_failed",
                                  arch=package.arch, branch=package.branch,
                                  pkgname=package.pkgname,
                                  version=package.version)
            session.merge(package)
        session.commit()

    def get_link(self, job_id):
        return ("file://" + bpo.config.args.temp_path + "/local_job_logs/" +
                str(job_id) + ".txt")
