from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.config.args
import bpo.jobs.get_depends
import bpo.db
import bpo.helpers.repo
import bpo.helpers.queue

callbacks = Blueprint('callbacks', __name__)


@callbacks.route('/api/job-callback/get_depends')
@header_auth('X-BPO-Token', "job_callback")
def after_get_depends():
    # Insert all depends, start next build
    bpo.db.insert_depends()
    bpo.helpers.repo.build()

    return 'warming up build servers...'


@callbacks.route('/api/job-callback/build_package')
@header_auth('X-BPO-Token', "job_callback")
def after_build_package():
    # TODO:
    # * save file to disk
    # * get queue_id from handler
    # * only mark as BUILT, if this was the last file (do we send multiple?)
    queue_id = 1
    queue_entry = bpo.helpers.queue.get_entry_by_id(queue_id)
    if not queue_entry:
        raise RuntimeError("invalid queue_id. FIXME: return error to user!")

    bpo.helpers.queue.set_status(queue_entry, "BUILT")
    bpo.helpers.repo.index(queue_entry["arch"])

    return 'package received, kthxbye'


@callbacks.route('/api/job-callback/sign_index')
@header_auth('X-BPO-Token', "job_callback")
def after_sign_index():
    # TODO:
    # * save index on disks
    # * get arch from handler
    arch = "x86_64"
    bpo.helpers.repo.publish(arch)

    return "alright, rollin' out the new repo"
