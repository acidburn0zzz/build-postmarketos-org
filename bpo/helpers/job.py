# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import importlib
import logging
import threading

import bpo.config.args

jobservice = None


def get_job_service():
    global jobservice
    if jobservice is None:
        name = bpo.config.args.job_service
        module = "bpo.job_services." + name
        jsmodule = importlib.import_module(module)
        jsclass = getattr(jsmodule, '{}JobService'.format(name.capitalize()))
        jobservice = jsclass()
    return jobservice


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
        if line[:spaces] == " " * spaces:
            ret += line[spaces:] + "\n"
        else: # Line does not start with indent
            ret += line + "\n"

    # Remove trailing empty lines
    while ret.endswith("\n\n"):
        ret = ret[:-1]

    return ret


def run(name, tasks, branch=None, arch=None, pkgname=None, version=None):
    """ :param branch: of the build package job, so we can copy the right
                       subdir of the WIP repository to the local packages dir
                       (relevant for running with local job service only).
        :returns: ID of the generated job, as passed by the backend """
    logging.info("[" + bpo.config.args.job_service + "] Run job: " + name)
    js = get_job_service()

    # TODO: some database foo, kill existing job etc.
    # TODO: add timeout for the job, and retries?

    # Job service specific setup task
    script_setup = remove_additional_indent(js.script_setup(branch), 8)
    tasks_formatted = collections.OrderedDict([("setup", script_setup)])

    # Format input tasks
    for task, script in tasks.items():
        tasks_formatted[task] = remove_additional_indent(script)

    # Pass to bpo.job_services.(...).run_job()
    job_id = js.run_job(name, tasks_formatted)
    logging.info("=> job id: " + str(job_id))

    bpo.ui.log_and_update(action="job_" + name, arch=arch, branch=branch,
                          pkgname=pkgname, version=version)

    return job_id


def update_package_status_after_restart():
    get_job_service().update_package_status_after_restart()
