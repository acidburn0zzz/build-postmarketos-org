# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import shlex
import subprocess

import bpo.helpers.config


def add_args_parser(parser):
    sub = parser.add_parser("local", help="run all jobs locally (debug)")
    parent_dir = os.path.realpath(bpo.helpers.config.bpo_src + "/../..")

    # --pmaports
    pma_default = parent_dir + "/pmaports"
    sub.add_argument("--pmaports", default=pma_default, dest="local_pmaports",
                     help="path to local pmaports.git checkout, the job will"
                          " run on a copy (default: " + pma_default + ")")

    # --pmbootstrap
    pmb_default = parent_dir + "/pmbootstrap/pmbootstrap.py"
    sub.add_argument("--pmbootstrap", default=pmb_default,
                     dest="local_pmbootstrap",
                     help="path to local pmbootstrap script to run" +
                          " (default: " + pmb_default + ")")

    # --tempdir
    tmp_default = os.path.realpath(bpo.helpers.config.bpo_src + "/../_job_tmp")
    sub.add_argument("--tempdir", default=tmp_default, dest="local_tempdir",
                     help="path to local temp dir for running jobs (will get"
                          " wiped; default: " + tmp_default + ")")


def script_setup(args):
    """ Setup tempdir with copy of pmaports.git and symlink to pmbootstrap. """
    pmaports = shlex.quote(args.local_pmaports)
    pmbootstrap = shlex.quote(args.local_pmbootstrap)
    return """
        cp -r """ + pmaports + """ .
        ln -s """ + pmbootstrap + """ ./pmbootstrap.py
    """


def run_print(command):
    print("% " + " ".join(command))
    subprocess.run(command, check=True)


def run_job(args, name, tasks):
    # Create tempdir, where we can run the scripts
    if os.path.exists(args.local_tempdir):
        run_print(["sudo", "rm", "-rf", args.local_tempdir])
    run_print(["mkdir", "-p", args.local_tempdir])

    # Write each task's script into a temp file and run it
    temp_script = args.local_tempdir + "/.current_task.sh"
    for task, script in tasks.items():
        print("### Task: " + task + " ###")

        with open(temp_script, "w", encoding="utf-8") as handle:
            handle.write("cd " + shlex.quote(args.local_tempdir) + "\n" +
                         script)
        run_print(["sh", "-ex", temp_script])
