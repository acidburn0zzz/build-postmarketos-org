# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.db
import bpo.helpers.repo


def reply(args, handler):
    # TODO:
    # * save file to disk
    # * get queue_id from handler
    # * only mark as BUILT, if this was the last file (do we send multiple?)
    queue_id = 1
    queue_entry = bpo.helpers.queue.get_entry_by_id(args, queue_id)
    if not queue_entry:
        raise RuntimeError("invalid queue_id. FIXME: return error to user!")

    bpo.helpers.queue.set_status(args, queue_entry, "BUILT")
    bpo.helpers.repo.index(args, queue_entry["arch"])

    handler.send_response(200)
    handler.end_headers()
    handler.wfile.write("package received, kthxbye".encode("utf-8"))
