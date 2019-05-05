# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import bpo.db
import bpo.helpers.repo


def reply(args, handler):
    # TODO:
    # * save index on disks
    # * get arch from handler
    arch = "x86_64"
    
    handler.send_response(200)
    handler.end_headers()
    handler.wfile.write("alright, rollin' out the new repo".encode("utf-8"))

    bpo.helpers.repo.publish(args, arch)
