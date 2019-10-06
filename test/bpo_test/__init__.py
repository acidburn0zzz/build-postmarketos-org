# Copyright 2019 Oliver Smith
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


def finish(*args, **kwargs):
    """ Use this for monkeypatching the bpo code, so a function finishes the
        test instead of performing the original functionallity. For example,
        when testing the gitlab api push hook, we can use this to prevent bpo
        from building the entire repo. """
    global result_queue
    logging.info("Thread finishes test: " + threading.current_thread().name)
    result_queue.put(True)


def finish_nok(*args, **kwargs):
    global result_queue
    name = threading.current_thread().name
    logging.info("Thread finishes test with NOK: " + name)
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
            sys.argv = ["bpo.py", "-t", "test/test_tokens.cfg", "local"]
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
        # Wait until result_queue is set with bpo_test.finish()
        result = result_queue.get()
        result_queue.task_done()
        self.thread.srv.shutdown()
        assert(result)
