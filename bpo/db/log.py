# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging


def insert(args, action, details=None, payload=None, commit=True):
    logging.info("Log insert: " + action)

    if details:
        details = json.dumps(details)
    if payload:
        payload = json.dumps(payload)

    args.db.cursor().execute(""" INSERT INTO log
                                    (datetime, action, details, payload)
                                 VALUES (DATETIME('now', 'localtime'), ?, ?, ?)
                             """, (action, details, payload))

    if commit:
        args.db.commit()
