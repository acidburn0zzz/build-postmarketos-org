# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import functools
import hashlib
import http.server
import json
import logging
import socketserver
import secrets

def reply(handler, status_code, message):
    handler.send_response(status_code)
    handler.end_headers()
    handler.wfile.write(message.encode("utf-8"))


def reply_404(handler):
    reply(handler, 404, "Nope, that isn't here")


def check_auth(handler, header, hash_valid):
    """ Validate authentication header, and send appropriate error responses.
        :param handler: bpo_handler instance
        :param header: the header to check (e.g. "X-Gitlab-Token")
        :param hash_valid: what to check against, for example:
                           args.token_hash_push_hook_gitlab
        :returns: True if authenticated, False otherwise """
    # Missing header
    if header not in handler.headers:
        reply(handler, 400, "Missing header: " + header)
        return False

    # Validate header
    hash_unknown = hashlib.sha512(handler.headers[header].encode()).hexdigest()
    if not secrets.compare_digest(hash_valid, hash_unknown):
        reply(handler, 401, "Invalid auth token")
        return False

    return True


def parse_payload(handler, required_keys):
    content_length = int(handler.headers["Content-Length"])
    post_data = handler.rfile.read(content_length)

    try:
        ret = json.loads(post_data)
    except json.JSONDecodeError:
        reply(handler, 406, "Your JSON is garbage")
        return None

    for key in required_keys:
        if key not in ret:
            reply(handler, 406, "Missing JSON key: " + key)
            return None

    return ret


class bpo_handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, bpo_args, *args, **kwargs):
        self.bpo_args = bpo_args
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Other URLs: not implemented
        reply_404(self)

    def do_POST(self):
        # API calls
        # TODO: starting with job_callback/ -> check auth
        args = self.bpo_args
        if self.path in args.api:
            return args.api[self.path](args, self)

        # Other URLs: not implemented
        reply_404(self)


def run(args):
    # Pass args to handler (https://stackoverflow.com/a/52046062)
    handler = functools.partial(bpo_handler, args)

    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        logging.info("Listening on {}:{}".format(args.host, args.port))
        httpd.serve_forever()
