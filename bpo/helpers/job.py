# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import importlib
import logging

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
        else:  # Line does not start with indent
            ret += line + "\n"

    # Always have one new line at the end
    ret += "\n"

    # Remove trailing empty lines
    while ret.endswith("\n\n"):
        ret = ret[:-1]

    return ret


def run(name, note, tasks, branch=None, arch=None, pkgname=None,
        version=None):
    """ :param note: what to send to the job service as description, rendered
                     as markdown in sourcehut
        :param branch: of the build package job, so we can copy the right
                       subdir of the WIP repository to the local packages dir
                       (relevant for running with local job service only).
        :returns: ID of the generated job, as passed by the backend """
    logging.info("[{}] Run job: {} ({})".format(bpo.config.args.job_service,
                                                note, name))
    js = get_job_service()

    # TODO: some database foo, kill existing job etc.
    # TODO: add timeout for the job, and retries?

    # Format input tasks
    tasks_formatted = collections.OrderedDict()
    for task, script in tasks.items():
        tasks_formatted[task] = remove_additional_indent(script)

    # Pass to bpo.job_services.(...).run_job()
    job_id = js.run_job(name, note, tasks_formatted)

    bpo.ui.log("job_" + name, arch=arch, branch=branch, pkgname=pkgname,
               version=version, job_id=job_id)

    return job_id


def update_package_status():
    logging.info("Checking if 'building' packages have failed or finished")
    building = bpo.db.PackageStatus.building
    js = get_job_service()

    session = bpo.db.session()
    result = session.query(bpo.db.Package).filter_by(status=building).all()
    for package in result:
        status_new = js.get_status(package.job_id)
        if status_new == building:
            continue
        bpo.db.set_package_status(session, package, status_new)
        action = "job_update_package_status_" + status_new.name
        bpo.ui.log_package(package, action)
    session.commit()


def get_link(job_id):
    """ :returns: the web link, that shows the build log """
    return get_job_service().get_link(job_id)


def init():
    """ Initialize the job service (make sure that tokens are there etc.) """
    return get_job_service().init()
