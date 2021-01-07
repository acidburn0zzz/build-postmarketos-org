# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import hashlib
from functools import wraps
from hmac import compare_digest
from flask import request, abort

import bpo.config.tokens


def header_auth(header, token):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if header not in request.headers:
                abort(400, 'Missing header: {}'.format(header))

            plain_input = request.headers[header].encode()
            hash_input = hashlib.sha512(plain_input).hexdigest()
            hash_valid = getattr(bpo.config.tokens, token)
            if not compare_digest(hash_input, hash_valid):
                return abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
