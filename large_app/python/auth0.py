from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin

from jose import jwt
import requests

import env
from jwks import jwks

log = logging.getLogger(__name__)


def auth0_url(path=""):
    return urljoin(f"https://{env.AUTH0_DOMAIN}/", path)


@dataclass
class TokenResult:
    access_token: dict
    id_token: dict
    result: dict

    @property
    def subject(self) -> str:
        return self.access_token["sub"]

    @property
    def expires(self) -> datetime:
        return datetime.utcfromtimestamp(self.access_token["exp"])

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires

    @property
    def token_type(self) -> str:
        return self.result["token_type"]

    @property
    def access_token_value(self) -> str:
        return self.result["access_token"]


def token_from_username_password(username, password) -> TokenResult:
    r = requests.post(
        auth0_url("oauth/token"),
        json={
            "grant_type": "password",
            "username": username,
            "password": password,
            "audience": env.AUTH0_API_AUDIENCE,
            "client_id": env.AUTH0_CLIENT_ID,
            "scope": "openid",
            "client_secret": env.AUTH0_CLIENT_SECRET,
        },
    )

    if r.status_code == 403:
        raise AuthError(r.json(), 401, reauth=True)
    parse_status_code(r)

    return _oauth_token_to_token_result(r.json())


def token_info_from_client_credentials(client_id, client_secret) -> dict:
    r = requests.post(
        auth0_url("oauth/token"),
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": env.AUTH0_ZEAPI_AUDIENCE,
        },
    )
    r.raise_for_status()

    token_info = r.json()
    log.info("Credentials login result: %s", token_info)

    return token_info


def token_result_from_client_credentials(
    client_id, client_secret
) -> TokenResult:
    token_info = token_info_from_client_credentials(client_id, client_secret)

    return TokenResult(
        access_token=parse_it(
            token_info["access_token"], env.AUTH0_ZEAPI_AUDIENCE
        ),
        id_token={},
        result=token_info,
    )


def _oauth_token_to_token_result(
    token_info: dict, audience=env.AUTH0_API_AUDIENCE
) -> TokenResult:
    assert "access_token" in token_info

    return TokenResult(
        access_token=parse_it(
            token_info["access_token"], env.AUTH0_API_AUDIENCE
        ),
        id_token=parse_it(token_info["id_token"], env.AUTH0_CLIENT_ID),
        result=token_info,
    )


def token_from_header_value(token, audience=env.AUTH0_API_AUDIENCE) -> dict:
    return parse_it(token, audience)


def token_result_from_header_value(
    token, audience=env.AUTH0_API_AUDIENCE
) -> TokenResult:
    return TokenResult(
        access_token=token_from_header_value(token, audience),
        id_token={},
        result={"access_token": token},
    )


def get_userinfo(token) -> dict:

    return requests.get(
        auth0_url("userinfo"), headers={"Authorization": f"Bearer {token}"}
    ).json()


def parse_it(token, audience) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=env.AUTH0_ALGORITHMS,
                audience=audience,
                issuer=auth0_url(),
            )
        except jwt.ExpiredSignatureError:
            raise AuthError(
                {"code": "token_expired", "description": "token is expired"},
                401,
            )
        except jwt.JWTClaimsError as claims_error:
            raise AuthError(
                {
                    "code": "invalid_claims",
                    "description": "incorrect claims,"
                    "please check the audience and issuer",
                },
                401,
            ) from claims_error
        except Exception:
            raise AuthError(
                {
                    "code": "invalid_header",
                    "description": "Unable to parse authentication" " token.",
                },
                401,
            )

        return payload

    raise AuthError(
        {
            "code": "invalid_header",
            "description": "Unable to find appropriate key",
        },
        401,
    )


class ManagementAPI(object):
    def __init__(self):
        self.grant_type = "client_credentials"
        self._current_access_token = None
        self._api_base = auth0_url("api/v2/")
        self._users_api_url = urljoin(self._api_base, "users")

    def _access_token(self):
        if self._current_access_token:
            expire_max = self._current_access_token.expires + timedelta(
                minutes=30
            )

            if expire_max > datetime.utcnow():
                log.debug(
                    "ManagementAPI token expires soon(%s). Renewing",
                    self._current_access_token.expires,
                )
                self._renew()
        else:
            self._renew()

        return self._current_access_token

    def _renew(self):
        res = requests.post(
            auth0_url("oauth/token"),
            json=dict(
                grant_type=self.grant_type,
                client_id=env.AUTH0_CLIENT_ID,
                client_secret=env.AUTH0_CLIENT_SECRET,
                audience=self._api_base,
            ),
        )

        if res.status_code > 299:
            log.warning(
                "Failed to get token for management api: %r", res.content
            )
        parse_status_code(res)

        token_info = res.json()
        self._current_access_token = TokenResult(
            access_token=parse_it(token_info["access_token"], self._api_base),
            id_token={},
            result=token_info,
        )

    def _headers(self):
        token = self._access_token()

        return {
            "Authorization": f"{token.token_type} {token.access_token_value}"
        }

    def create_user(self, user, password: str):
        res = requests.post(
            self._users_api_url,
            json={
                "email": user.email,
                "password": password,
                "connection": env.AUTH0_UP_CONNECTION_NAME,
                "user_metadata": user.dump(),
            },
            headers=self._headers(),
        )

        if res.status_code > 299:
            log.warning(
                "Got %r",
                res.content,
                extra={
                    "auth0_create_user_context": {
                        "user_id": user.id,
                        "email": user.email,
                        "name": user.name,
                    }
                },
            )
        parse_status_code(res)

        return res.json()

    def get_userinfo(self, sub: str):
        res = requests.get(
            urljoin(self._users_api_url.rstrip("/") + "/", sub),
            headers=self._headers(),
        )
        parse_status_code(res)

        userinfo_result = res.json()
        # Paste over the main difference between id_token and userinfo
        userinfo_result.setdefault("sub", userinfo_result.get("user_id"))

        return userinfo_result


class AuthError(Exception):
    def __init__(self, error, status_code, reauth=False):
        self.error = error
        self.status_code = status_code
        self.reauth = reauth


def parse_status_code(res):
    if res.status_code in (409, 400, 429):  # duplicate user
        raise AuthError(error=res.json(), status_code=res.status_code)

    res.raise_for_status()


def request_bearer_token(request) -> str:
    header = request.headers.get("authorization", "")

    if not header.lower().startswith("bearer"):
        return None

    _, header_token = header.split(" ", 1)

    return header_token


management_api = ManagementAPI()
