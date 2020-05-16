# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import threading
import logging
import os
import queue
import shutil
import sys
import werkzeug.serving

# Add topdir to import path
topdir = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/../.."))
sys.path.insert(0, topdir)

# Use "noqa" to ignore "E402 module level import not at top of file"
import bpo  # noqa
import bpo.config.const  # noqa
import bpo.config.args  # noqa

# Queue for passing test result between threads
result_queue = None


def reset():
    """ Remove the database, generated binary packages and temp dirs. To be
        used at the start of test cases. """
    paths = [bpo.config.args.db_path,
             bpo.config.args.html_out,
             bpo.config.args.temp_path,
             bpo.config.args.repo_final_path,
             bpo.config.args.repo_wip_path,
             bpo.config.const.repo_wip_keys]

    logging.info("Removing all BPO data")
    for path in paths:
        if not os.path.exists(path):
            logging.debug(path + ": does not exist, skipping")
            continue
        if os.path.isdir(path):
            logging.debug(path + ": removing path recursively")
            shutil.rmtree(path)
        else:
            logging.debug(path + ": removing file")
            os.unlink(path)


def nop(*args, **kwargs):
    """ Use this for monkeypatching the bpo code, so a function does not do
        anything. For example, when testing the gitlab api push hook, we can
        use this to prevent bpo from building the entire repo. """
    logging.info("Thread called nop: " + threading.current_thread().name)


def true(*args, **kwargs):
    """ Use this for monkeypatching the bpo code, so a function always returns
        True. """
    logging.info("Thread called true: " + threading.current_thread().name)
    return True


def stop_server(*args, **kwargs):
    """ Use this for monkeypatching the bpo code, so a function finishes the
        test instead of performing the original functionallity. For example,
        when testing the gitlab api push hook, we can use this to prevent bpo
        from building the entire repo. """
    global result_queue
    logging.info("Thread stops bpo server: " + threading.current_thread().name)
    result_queue.put(True)


def stop_server_nok(*args, **kwargs):
    global result_queue
    name = threading.current_thread().name
    logging.info("Thread stops bpo server, NOK: " + name)
    result_queue.put(False)


def raise_exception(*args, **kwargs):
    raise bpo.helpers.ThisExceptionIsExpectedAndCanBeIgnored("ohai")


class BPOServer():
    """ Run the flask server in a second thread, so we can send requests to it
        from the main thread. Use this as "with statement", i.e.:

        with bpo_test.BPO_Server():
            requests.post("http://127.0.0.1:5000/api/push-hook/gitlab")

        Based on: https://stackoverflow.com/a/45017691 """
    thread = None

    class BPOServerThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)
            os.environ["FLASK_ENV"] = "development"
            sys.argv = ["bpo.py", "-t", "test/test_tokens.cfg", "--mirror", "",
                        "local"]
            app = bpo.main(True)
            self.srv = werkzeug.serving.make_server("127.0.0.1", 5000, app,
                                                    threaded=False)
            self.ctx = app.app_context()
            self.ctx.push()

        def run(self):
            self.srv.serve_forever()

    def __init__(self):
        global result_queue
        reset()
        result_queue = queue.Queue()
        self.thread = self.BPOServerThread()

    def __enter__(self):
        self.thread.start()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        global result_queue
        # Wait until result_queue is set with bpo_test.stop_server()
        result = result_queue.get()
        result_queue.task_done()
        self.thread.srv.shutdown()
        assert result


def assert_package(pkgname, arch="x86_64", branch="master", status=None,
                   version=None, exists=True, retry_count=0, job_id=False):
    """ Verify that a package exists, and optionally, that certain attributes
        are set to an expected value. This function is called assert_* but we
        are actually raising exceptions, because we can test if they get thrown
        and the error message can be more descriptive.

        :param pkgname: package name (e.g. "hello-world")
        :param arch: package architecture
        :param branch: pmaports.git branch
        :param status: bpo.db.PackageStatus string, e.g. "built"
        :param version: package version, e.g. "1-r4"
        :param exists: set to False if the package should not exist at all
        :param retry_count: how often build failed previously
        :param job_id: the job_id, set to None or an integer to check """
    session = bpo.db.session()
    package = bpo.db.get_package(session, pkgname, arch, branch)

    if not exists:
        if not package:
            return
        raise RuntimeError("Package should NOT exist in db: {}/{}/{}".format(
            branch, arch, pkgname))

    if package is None:
        raise RuntimeError("Expected package to exist in db: {}/{}/{}".format(
            branch, arch, pkgname))

    if status:
        status_value = bpo.db.PackageStatus[status]
        if(package.status != status_value):
            raise RuntimeError("Expected status {}, but has {}: {}".format(
                status, package.status.name, package))

    if version and package.version != version:
        raise RuntimeError("Expected version {}: {}".format(version, package))

    if package.retry_count != retry_count:
        raise RuntimeError("Expected retry_count {}: {}"
                           .format(retry_count, package))

    if job_id is not False and package.job_id != job_id:
        raise RuntimeError("Expected job_id {}: {}".format(job_id, package))
