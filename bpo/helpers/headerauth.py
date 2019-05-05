from functools import wraps
from hmac import compare_digest
from flask import g, request, abort


def header_auth(header, value):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if header not in request.headers:
                abort(400, 'Missing header: {}'.format(header))
            if not compare_digest(request.headers[header], value):
                return abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
