import logging

import auth0
from models import Auth0Mapping, db, User

log = logging.getLogger(__name__)


def request_bearer_token(request) -> str:
    header = request.headers.get("authorization", "")

    if not header.lower().startswith("bearer"):
        return None

    _, header_token = header.split(" ", 1)

    return header_token


def user_from_access_token(request) -> User:
    header_token = request_bearer_token(request)

    if not header_token:
        return None

    auth_info = auth0.token_from_header_value(header_token)
    mapping = Auth0Mapping.get_from_sub(auth_info["sub"])

    if mapping:
        return mapping.user

    user_info = auth0.management_api.get_userinfo(auth_info["sub"])
    log.info(
        "Didn't find a user for authenticated user %s. Fetched userinfo %s",
        auth_info,
        user_info,
    )

    with db as session:
        user, update = User.from_auth0(user_info)

        if not update:
            session.add(user)
        session.commit()
        session.refresh(user)

    return user
