from functools import wraps
import logging

from flask import make_response, request
from flask_apispec import doc as _doc

log = logging.getLogger(__name__)


def docer(*tags):
    def doc(*args, **kwargs):
        kwargs.setdefault("tags", tags)
        login_required = kwargs.pop("login_required", True)
        stub = kwargs.pop("stub", True)

        if stub:
            kwargs.setdefault("description", "")
            kwargs["description"] += '<h1 style="color: red">STUB</h1>'

        if login_required:
            kwargs.setdefault("security", []).extend(
                [dict(httpBasic=[]), dict(auth0=[])]
            )

        return _doc(*args, **kwargs)

    return doc


def not_implemented(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        log.warning(
            "%s %s: Not Implemented (%s)",
            request.method,
            request.path,
            request.endpoint,
            extra=kwargs,
        )

        return f(*args, **kwargs)

    return wrapper


def empty_204():
    return make_response("", 204)
