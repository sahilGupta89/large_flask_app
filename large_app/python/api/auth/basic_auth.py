from dataclasses import dataclass
import logging

import auth0
from models import Auth0Mapping, BasicCache, db, User

log = logging.getLogger(__name__)


@dataclass
class BasicAuthResult:
    user: User
    token_result: auth0.TokenResult


def user_from_basic_auth_request(request) -> User:
    basic_auth_result = request_to_auth_result(request)

    return basic_auth_result.user if basic_auth_result else None


def request_to_auth_result(request) -> BasicAuthResult:
    rauth = request.authorization

    if not rauth:
        return None

    username = rauth["username"]
    password = rauth["password"]

    return userpw_to_auth_result(username, password)


def userpw_to_auth_result(username, password) -> BasicAuthResult:

    try:
        return verify_basic_auth(username, password)
    except Exception:
        log.info(
            "Failed to parse %s for username/password", username, exc_info=True
        )
        raise


def verify_basic_auth(username, password) -> BasicAuthResult:
    """ Take username and password and use all available methods to find a
    BasicAuthResult

    Throws: AuthError on errors from auth0 SaaS
    """
    token_result = _token_result(username, password)
    mapping = _find_any_exiting_mapping_and_refresh_user(token_result)

    if mapping:
        return BasicAuthResult(user=mapping.user, token_result=token_result)

    log.info(
        "No mapping for %s(%s). Creating mapping",
        username,
        token_result.id_token,
    )
    user = _create_user_from_auth0(token_result)

    return BasicAuthResult(user=user, token_result=token_result)


def _token_result(username, password) -> auth0.TokenResult:
    # 1) Get the tokens from cache or auth0
    token_result = BasicCache.verify(username, password)

    if not token_result:
        token_result = fetch_and_cache_auth0_token(username, password)

    return token_result


def _find_any_exiting_mapping_and_refresh_user(token_result) -> Auth0Mapping:
    # 2) find the mapping between auth0 user and "our user" (in db)
    mapping = Auth0Mapping.get_from_sub(token_result.subject)

    if mapping:
        # 2.1 Refresh userinfo based of auth0 info (auth0 is authorative on
        # data)
        update_user_from_token(mapping, token_result.id_token)

    return mapping


def _create_user_from_auth0(token_result):
    # 3) If the mapping wasn't found but auth0 knows the user,
    # create the mapping

    with db as session:
        user, update = User.from_auth0(
            auth0.management_api.get_userinfo(token_result.subject)
        )

        if not update:
            session.add(user)
        session.commit()
        session.refresh(user)

    return user


def fetch_and_cache_auth0_token(username, password) -> auth0.TokenResult:
    token_result = auth0.token_from_username_password(username, password)
    with db as session:
        pruned = False

        for p in BasicCache.prunable():
            log.info("Pruned %s %s %s", p, p.expired, p.expires)
            session.delete(p)
            pruned = True

        if pruned:
            session.commit()
        cur = BasicCache.query.get(username)

        if cur:
            log.info("Forcefully expired %s", cur)
            session.delete(cur)
        session.add(BasicCache.create(username, password, token_result))
        session.commit()

    return token_result


def update_user_from_token(mapping, id_token) -> None:
    with db as session:
        mapping.user.update_from_auth0(id_token)
        session.commit()
        session.refresh(mapping.user)
