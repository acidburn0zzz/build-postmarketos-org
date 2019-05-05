# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import logging


def remove_additional_indent(script, spaces=12):
    """ Remove leading spaces and leading/trailing empty lines from script
        parameter. This is used, so we can use additional indents when
        embedding shell code in the python code. """
    ret = ""
    for line in script.split("\n"):
        # Remove leading empty lines
        if not line and not ret:
            continue

        # Remove additional indent from line
        ret += line[spaces:] + "\n"

    # Remove trailing empty lines
    while ret.endswith("\n\n"):
        ret = ret[:-1]

    return ret


def run(args, name, tasks):
    logging.info("[" + args.job_service + "] Run job: " + name)

    # TODO: some database foo, kill existing job etc.
    # TODO: add timeout for the job, and retries?

    # Job service specific setup task
    script_setup = args.job_service_module.script_setup(args)
    tasks_formatted = {"setup": remove_additional_indent(script_setup, 8)}

    # Format input tasks
    for task, script in tasks.items():
        tasks_formatted[task] = remove_additional_indent(script)

    # Pass to bpo.job_services.(...).run_job()
    args.job_service_module.run_job(args, name, tasks_formatted)
