from flask import current_app, Response
from flask_login import LoginManager

from models import User
from . import basic_auth
from . import token_auth

login_manager = LoginManager()


@login_manager.request_loader
def load_user_from_auth_header(req) -> User:
    """Try via both http basic check and token auth to get a user object from
    our database to match an authorized user"""

    methods = [
        basic_auth.user_from_basic_auth_request,
        token_auth.user_from_access_token,
    ]

    for method in methods:
        user = method(req)

        if user:
            return user

    # Failed to get decent login

    if req.headers.get("authorization"):
        current_app.logger.warning(
            "Failed login for %s", (req.authorization or {}).get("username")
        )

    return None


@login_manager.unauthorized_handler
def unauth():
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )
