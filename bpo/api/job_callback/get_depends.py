# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.db
import bpo.helpers.repo


def reply(args, handler):
    # Insert all depends, start next build
    bpo.db.insert_depends(args)
    bpo.helpers.repo.build(args)

    handler.send_response(200)
    handler.end_headers()
    handler.wfile.write("depends received!".encode("utf-8"))
