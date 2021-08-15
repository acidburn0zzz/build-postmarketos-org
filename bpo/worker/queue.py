# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" The web API thread and ImageTimerThread call various add_* functions from
    this file, to put a new task into the worker's queue. """
import collections
import enum
import logging
import threading

import bpo.worker

# Each entry in tasks:
# {"action": QueueAction entry, "args": args, "kwargs": kwargs}
tasks = collections.deque()
cond = threading.Condition()


class QueueAction(enum.Enum):
    IMAGES_QUEUE_FILL = enum.auto()
    UI_LOG = enum.auto()
    UI_UPDATE = enum.auto()
    WORKER_STOP_THREAD = enum.auto()


def get_task():
    """ Block until receiving a new task, to be called by the worker thread.
        :returns: the task """
    global cond
    global tasks

    ret = None

    with cond:
        if not tasks:
            logging.debug("WorkerThread's queue is empty, sleeping")
            cond.wait()
        ret = tasks.pop()

    if ret:
        logging.debug(f"- worker queue: action={ret['action'].name},"
                      f" args={ret['args']},"
                      f" kwargs={ret['kwargs']}")
    return ret


def _add(__queue_add_action, *args, **kwargs):
    global cond
    global tasks

    # Don't just call it "action" to avoid conflicts with kwargs
    action = __queue_add_action

    logging.debug(f"+ worker queue: action={action.name},"
                  f" args={args},"
                  f" kwargs={kwargs}")
    with cond:
        tasks.appendleft({"action": action,
                          "args": args,
                          "kwargs": kwargs})
        cond.notify()


def add_images_queue_fill(*args, **kwargs):
    _add(QueueAction.IMAGES_QUEUE_FILL, *args, **kwargs)


def add_ui_log(*args, **kwargs):
    _add(QueueAction.UI_LOG, *args, **kwargs)


def add_ui_update():
    _add(QueueAction.UI_UPDATE)


def add_worker_stop_thread():
    """ Stop the worker thread and block until it is stopped. """
    if not bpo.worker.thread:
        logging.debug("WorkerThread is not running (nothing to stop)")
        return

    _add(QueueAction.WORKER_STOP_THREAD)
    logging.debug("Waiting until WorkerThread has stopped")

    with cond:
        cond.wait()
        assert not tasks, "queue is not empty after WorkerThread was stopped!"

    logging.debug("WorkerThread has stopped")
