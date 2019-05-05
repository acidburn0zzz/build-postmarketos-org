# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import secrets
import bpo.db.log
import bpo.helpers.httpd
import bpo.jobs.get_depends

"""
https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#push-events
"""

def reply(args, handler):
    # Verify auth token
    if not bpo.helpers.httpd.check_auth(handler, "X-Gitlab-Token",
                                        args.token_hash_push_hook_gitlab):
        return

    # Get payload
    required_keys = ["checkout_sha", "commits", "object_kind"]
    payload = bpo.helpers.httpd.parse_payload(handler, required_keys)
    if not payload:
        return

    # Verify payload
    if payload["object_kind"] != "push":
        bpo.helpers.httpd.reply(handler, 406, "Unknown object_kind")
        return

    # Checks passed, send answer
    bpo.helpers.httpd.reply(handler, 200, "triggered!")

    # Write to DB
    bpo.db.log.insert(args, "push_hook_gitlab", payload=payload)

    # Run depends job
    bpo.jobs.get_depends.run(args)
