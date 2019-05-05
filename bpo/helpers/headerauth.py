from functools import wraps
from hmac import compare_digest
from flask import g, request, abort

from bpo.helpers import config


def header_auth(header, config_key):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if getattr(config, config_key) is None:
                abort(500, 'Server config incomplete')
            value = getattr(config, config_key)
            if header not in request.headers:
                abort(400, 'Missing header: {}'.format(header))
            if not compare_digest(request.headers[header], value):
                return abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
