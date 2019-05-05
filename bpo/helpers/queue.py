# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging


def set_status(queue_entry, status):
    logging.info("STUB: bpo.queue.set_status()")
    # TODO: status == BUILT: update timestamp too


def get_entry_next(arch):
    logging.info("STUB: bpo.queue.get_entry_next()")
    return {"pkgname": "hello-world",
            "pkgver": "1",
            "pkgrel": "3",
            "arch": "x86_64",
            "id": 1234}


def get_entry_by_id(queue_id):
    logging.info("STUB: bpo.queue.get_entry_by_id()")
    return {"pkgname": "hello-world",
            "pkgver": "1",
            "pkgrel": "3",
            "arch": "x86_64",
            "id": 1234}
