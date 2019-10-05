""" Model for the User """
from datetime import datetime
import hashlib
import logging
import os

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import true
from sqlalchemy.types import CHAR, LargeBinary

import auth0
from .database import db
from .mixins import StandardObjectMixin

log = logging.getLogger(__name__)


class UserLocation(StandardObjectMixin, db.Model):
    __tablename__ = "user_location"
    name = db.Column(Text, nullable=False)
    street = db.Column(Text)
    city = db.Column(Text)
    country = db.Column(
        CHAR(2),
        comment="ISO-3166-1 2alpha encoding",
        doc="ISO-3166-1 2 alpha encoded country",
    )
    primary = db.Column(
        db.Boolean, default=False, server_default="false", nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class User(StandardObjectMixin, UserMixin, db.Model):
    __tablename__ = "user"
    name = db.Column(Text, nullable=False)
    phone = db.Column(Text)
    email = db.Column(Text, unique=True, nullable=False)
    locale = db.Column(Text)
    terms_accept = db.Column(Boolean)
    terms_accept_at = db.Column(DateTime)

    alert_subscriptions = db.relationship("AlertSubscription", lazy="joined")
    # auth0_mapping = db.relationship("Auth0Mapping", uselist=False)
    locations = db.relationship(UserLocation, lazy="joined")

    @classmethod
    def from_auth0(cls, user_info) -> ("User", bool):
        """
        Take an auth0 userinfo/id_token and create a user based off that
        information

        Special casing for existing users without mapping

        Returns: the User and a flag stating if it's a new user or an updated
        user"
        """
        update = False
        email = user_info["email"]
        user = cls.query.filter(
            db.func.lower(cls.email) == email.lower()
        ).one_or_none()

        if not user:
            user = cls(**_relevant_user_info_fields(user_info))
        else:
            update = True
            user.update_from_auth0(user_info)
            log.warning(
                "%s already existed. Refreshed values. Adding mapping", email
            )
        user.add_mapping(user_info["sub"])

        return user, update

    def update_from_auth0(self, user_info) -> bool:
        """ Update current user with info from userinfo/id_token"""

        changed = False

        for k in _relevant_user_info_fields(user_info):
            value = user_info[k]

            if getattr(self, k) == value:  # Skip unchanged values
                continue

            log.info(
                "Setting %s to %s (was %s) for %s",
                k,
                value,
                getattr(self, k),
                self,
            )
            changed = True
            setattr(self, k, value)

        return changed

    def add_mapping(self, sub: str):
        self.auth0_mapping = Auth0Mapping(sub=sub)

        return self

    def exists(self):
        return (
            self.query.filter(
                db.func.lower(User.email) == db.func.lower(self.email)
            ).first()
            is not None
        )

    def dump(self):  # pragma: no cover
        return self.schema.dump(self).data


def _relevant_user_info_fields(user_info):
    return {
        k: v
        for k, v in {
            **user_info.get("user_metadata", {}),
            **user_info.get("app_metadata", {}),
            **user_info,
        }.items()
        if k in _user_fields
    }


_user_fields = [
    "name",
    "email",
    "phone",
    "locale",
    "terms_accept",
    "terms_accept_at",
]


class Auth0Mapping(db.Model):
    """ Mapping from Auth0 User ids to our users"""

    __tablename__ = "auth0_mapping"
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    sub = db.Column(db.Text, nullable=False)
    user = db.relationship(User, uselist=False)

    @classmethod
    def get_from_sub(cls, sub):
        return cls.query.filter(Auth0Mapping.sub == sub).one_or_none()


class BasicCache(db.Model):
    """Caching of basic credentials
    while we wait for them to be deprected in clients we don't want to hit
    auth0 apis for every single api request. This caches the auth0 response
    for as long as an access token survices
    """

    __tablename__ = "basic_cache"
    username = db.Column(db.Text, primary_key=True)
    hashed = db.Column(LargeBinary)
    salt = db.Column(LargeBinary)
    expires = db.Column(DateTime)
    access_token = db.Column(JSONB)
    id_token = db.Column(JSONB)
    result = db.Column(JSONB)

    @hybrid_property
    def expired(self):
        return self.expires <= datetime.utcnow()

    @classmethod
    def prunable(cls):
        """ List of all expired entries for pruning """

        return cls.query.filter(cls.expired == true())

    @classmethod
    def verify(cls, username, password) -> auth0.TokenResult:
        """ Clasic username/password verification against hash from db
        Returns: access_token, id_token pair
        """
        cur = cls.query.filter(cls.username == username).one_or_none()

        if not cur:
            return None

        if cur.expired:
            log.warning("%s expired", cur)

            return None

        got = _hash(password, cur.salt)

        if got == cur.hashed:
            return auth0.TokenResult(
                cur.access_token, cur.id_token, cur.result
            )
        else:
            log.warning("Didnt match %s %s", got, cur.hashed)

        return None

    @classmethod
    def create(
        cls, username: str, password: str, token_result: auth0.TokenResult
    ) -> "BasicCache":
        salt = os.urandom(32)

        return cls(
            username=username,
            salt=salt,
            expires=datetime.utcfromtimestamp(
                token_result.access_token["exp"]
            ),
            hashed=_hash(password, salt),
            access_token=token_result.access_token,
            id_token=token_result.id_token,
            result=token_result.result,
        )


def _hash(password, salt):
    return hashlib.pbkdf2_hmac(
        HASH_ALGO, password.encode(), salt, HASH_ITERATIONS
    )


HASH_ALGO = "sha256"  # as recommended by the docs
HASH_ITERATIONS = 100_000  # ^^