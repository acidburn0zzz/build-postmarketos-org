# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" WorkerThread has a queue, which gets filled by the web API and the
    ImagesTimerThread. The WorkerThread does database writes and file
    modifications. Other threads are only allowed to read from the database and
    to interact with files in unique temporary directories to avoid conflicts
    (#49, #79, #103)."""
import threading
import logging

import bpo.images.queue
import bpo.ui
import bpo.worker.queue

thread = None


def _action_images_queue_fill(*args, **kwargs):
    bpo.images.queue.fill(*args, **kwargs)


def _action_repo_build(*args, **kwargs):
    bpo.repo.build(*args, **kwargs)


def _action_ui_log(*args, **kwargs):
    bpo.ui.log(*args, **kwargs)


def _action_ui_update():
    bpo.ui.update()


class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="WorkerThread")

    def run(self):
        global thread

        while True:
            task = bpo.worker.queue.get_task()
            if not task:
                continue

            # Stop the thread
            if task["action"].name == "WORKER_STOP_THREAD":
                logging.debug("WorkerThread stopped")
                thread = None
                with bpo.worker.queue.cond:
                    bpo.worker.queue.cond.notify()
                return

            # Call _action_* from above
            action_func = f"_action_{task['action'].name.lower()}"
            getattr(bpo.worker, action_func)(*task["args"], **task["kwargs"])


def init():
    global thread

    assert(not thread)
    thread = WorkerThread()
    thread.start()


def is_other_thread():
    """ Test if the currently running thread is *not* the worker thread. To be
        used as follows:

        if bpo.worker.is_other_thread():
            return bpo.worker.queue.add_...()

        (other code that the worker thread should do)
    """
    return threading.current_thread() != thread


def assert_if_not_worker_thread():
    assert threading.current_thread() == thread, "this function must only be" \
            " called by the worker thread! go through bpo.worker.queue from" \
            " other threads (example: bpo.ui.log())"
