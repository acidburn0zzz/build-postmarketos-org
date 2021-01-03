# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import copy
import logging
import os
import requests
import shlex
import subprocess
import threading
import time

import bpo.config.args
import bpo.db
from bpo.job_services.base import JobService


# Instance of LocalJobServiceThread (created on demand)
thread = None

# When starting a job, the current ID increases by 1
job_id = 0

# The job queue. Jobs get added in the main thread, the LocalJobServiceThread
# starts queued jobs and updates their status. jobs_cond is used for locking.
# jobs[id] = {"name": ...,
#             "note": ...,
#             "tasks": [...],
#             "branch": ...,
#             "status": "queued" | "running" | "success" | "failed"}
# Set jobs to None to exit the LocalJobServiceThread (used in testsuite).
jobs = {}
jobs_cond = threading.Condition()


class LocalJobServiceThread(threading.Thread):
    """ Local jobs are running on the same machine, but in a different thread.
        New jobs can be queued while another job is running. They will be
        executed in sequence. """

    def __init__(self):
        threading.Thread.__init__(self, name="LocalJobService")

    def run_print(self, command):
        with open(self.log_path, "a") as handle:
            handle.write("% " + " ".join(command) + "\n")
            subprocess.run(command, check=True, stdout=handle, stderr=handle)

    def run_print_try(self, command):
        """ Try to execute a shell command.
            :returns: True if exit code is 0, False otherwise """
        try:
            # Put this in an extra function, so we can easily monkeypatch
            # it in the testsuite
            self.run_print(command)
            return True
        except Exception:
            return False

    def setup_task(self, branch):
        """ Setup temp_path with copy of pmaports.git/pmbootstrap.git and
            remove locally built packages.

            Optionally copy the WIP repository to the local packages dir, so we
            can build packages depending on others, without actually firing up
            a second webserver when testing locally and making the whole
            development / automated testing setup more complicated. When BPO is
            using a different backend than the local one (e.g. sourcehut), the
            WIP repository will not get copied over the local packages dir,
            instead it will get added as regular HTTPS mirror."""
        temp_path = bpo.config.args.temp_path + "/local_job"
        pmaports = bpo.config.args.local_pmaports
        pmbootstrap = bpo.config.args.local_pmbootstrap
        token = bpo.config.const.test_tokens["job_callback"]
        repo_wip_path = bpo.config.args.repo_wip_path
        repo_wip_key = bpo.config.const.repo_wip_keys + "/wip.rsa"
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
            mkdir build.postmarketos.org
            cp -r """ + shlex.quote(bpo.config.const.top_dir) + """/helpers \
                    build.postmarketos.org
            echo """ + shlex.quote(token) + """ > ./token
            ./pmbootstrap/pmbootstrap.py -q -y zap -p

            # Switch branch and release channel
            git -C pmaports checkout """ + shlex.quote(branch) + """
            channel="$(grep "^channel=" pmaports/pmaports.cfg | cut -d= -f 2)"

            # Copy WIP repo
            branch=""" + shlex.quote(branch) + """
            work_path="$(./pmbootstrap/pmbootstrap.py -q config work)"
            packages_path="$work_path/packages"
            repo_wip_path=""" + shlex.quote(repo_wip_path) + """
            if [ -n "$branch" ] && [ -d "$repo_wip_path/$branch" ]; then
                sudo mkdir -p "$packages_path/$channel"
                sudo cp -r "$repo_wip_path/$branch/"* \
                    "$packages_path/$channel"
                sudo chown -R """ + shlex.quote(uid) + """ "$packages_path"
            fi

            # Use WIP repo key as final repo key (it's fine for local testing)
            cp """ + shlex.quote(repo_wip_key) + """ .final.rsa
        """

    def run_job(self, name, note, tasks, branch, job_id):
        self.job_id = job_id

        # Prepare log
        self.log_path = (bpo.config.args.temp_path + "/local_job_logs/" +
                         str(job_id) + ".txt")
        logging.info("Job " + name + " started, logging to: " + self.log_path)

        # Begin with setup task
        tasks["setup"] = self.setup_task(branch)
        tasks.move_to_end("setup", last=False)

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
            export BPO_JOB_ID=""" + str(job_id) + """
            export BPO_JOB_NAME=""" + shlex.quote(name) + """
            export BPO_WIP_REPO_PATH=""" + shlex.quote(wip_repo_path) + """
            export BPO_WIP_REPO_URL="" # empty, because we copy it instead
            export BPO_WIP_REPO_ARG="" # empty, because we copy it instead
            export BPO_TIMEOUT="0.1"
            export BPO_TIMEOUT_IGNORE="1"
        """

        # Write each task's script into a temp file and run it
        temp_script = temp_path + "/current_task.sh"
        for task, script in tasks.items():
            print("### Task: " + task + " ###")

            with open(temp_script, "w", encoding="utf-8") as handle:
                handle.write("cd " + shlex.quote(temp_path) + "\n" +
                             env_vars + "\n" +
                             script)
            if not self.run_print_try(["sh", "-ex", temp_script]):
                logging.info("Job failed!")
                return False
        return True

    def run(self):
        global jobs
        global jobs_cond

        while True:
            # Copy the jobs dict before iterating over it, so we don't block it
            # while executing the job (and the other thread can happily queue
            # new jobs in the meantime).
            jobs_copy = None
            with jobs_cond:
                if jobs is None:
                    logging.debug("terminated")
                    jobs = {}
                    jobs_cond.notify()
                    break
                jobs_copy = copy.deepcopy(jobs)

            # Execute all queued jobs, one at a time
            for job_id, job_data in jobs_copy.items():
                if job_data["status"] != "queued":
                    continue

                # Extract job data
                name = job_data["name"]
                note = job_data["note"]
                tasks = job_data["tasks"]
                branch = job_data["branch"]
                logging.info("Received job: " + name + " (" + note + ")")

                # Set to running
                with jobs_cond:
                    # Check if LocalJobService must terminate
                    if jobs is None:
                        break
                    jobs[job_id]["status"] = "running"

                # Run the job
                success = self.run_job(name, note, tasks, branch, job_id)
                status = "success" if success else "failed"
                logging.info("Job finished (" + status + ")")

                # Set to success/failed
                with jobs_cond:
                    # Check if LocalJobService must terminate
                    if jobs is None:
                        break
                    jobs[job_id]["status"] = status

                # Notify API of failure (as the sourcehut job service would do)
                if status == "failed":
                    logging.debug("Telling bpo server that the job failed")
                    url = "http://{}:{}/api/public/update-job-status".format(
                        bpo.config.args.host, bpo.config.args.port)
                    try:
                        # The server may take long to answer (#49). We don't
                        # care about the answer here, so move on quickly.
                        requests.post(url, timeout=0.01)
                    except requests.exceptions.ReadTimeout:
                        logging.debug("BPO server takes long to answer,"
                                      " moving on...")
                        pass

            # Sleep before trying to find new jobs
            time.sleep(0.01)


class LocalJobService(JobService):

    def run_job(self, name, note, tasks, branch):
        global thread
        global job_id
        global jobs
        global jobs_cond

        job_id += 1

        # Prepare log dir, clear possibly existing log file
        log_path = (bpo.config.args.temp_path + "/local_job_logs/" +
                    str(job_id) + ".txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as handle:
            handle.write("job queued\n")

        # Add job to queue
        with jobs_cond:
            jobs[job_id] = {"name": name,
                            "note": note,
                            "tasks": tasks,
                            "branch": branch,
                            "status": "queued"}
            jobs_cond.notify()

        # Start thread
        if not thread:
            thread = LocalJobServiceThread()
            thread.start()

        return job_id

    def get_status(self, job_id_check):
        global job_id
        global jobs
        global jobs_cond

        # Job from previous bpo instance
        if job_id_check > job_id:
            return bpo.db.PackageStatus.failed

        with jobs_cond:
            status = jobs[job_id_check]["status"]

        # Convert the status string
        if status == "success":
            return bpo.db.PackageStatus.built
        if status == "failed":
            return bpo.db.PackageStatus.failed
        return bpo.db.PackageStatus.building

    def get_link(self, job_id):
        return ("file://" + bpo.config.args.temp_path + "/local_job_logs/" +
                str(job_id) + ".txt")


def stop_thread():
    global thread
    global job_id
    global jobs
    global jobs_cond

    if thread is None:
        logging.debug("LocalJobService isn't running")
        return

    # Set jobs to None, so LocalJobService stops
    logging.debug("Stopping LocalJobService...")
    with jobs_cond:
        thread = None
        jobs = None
        jobs_cond.notify()

    # Wait until LocalJobService has stopped and sets jobs back to {}
    logging.debug("Waiting until LocalJobService thread is stopped...")
    while True:
        time.sleep(0.01)
        with jobs_cond:
            if jobs == {}:
                logging.debug("LocalJobService thread has stopped")
                return
