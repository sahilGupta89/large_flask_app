""" Model for the User """
from datetime import datetime
import hashlib
import logging
import os

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Text, CHAR
from dataclasses import dataclass
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import true

from .database import db

from .mixins import StandardObjectMixin

log = logging.getLogger(__name__)



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
    locations = db.relationship(UserLocation, lazy="joined")

    def exists(self):
        return (
                self.query.filter(
                    db.func.lower(User.email) == db.func.lower(self.email)
                ).first()
                is not None
        )

    def dump(self):  # pragma: no cover
        return self.schema.dump(self).data


class BasicCache(db.Model):
    """Caching of basic credentials
    while we wait for them to be deprected in clients we don't want to hit
    auth0 apis for every single api request. This caches the auth0 response
    for as long as an access token survices
    """

    __tablename__ = "basic_cache"
    username = db.Column(db.Text, primary_key=True)
    hashed =  db.Column(db.LargeBinary)
    salt = db.Column(db.LargeBinary)
    expires = db.Column(db.DateTime)
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
    def verify(cls, username, password) -> TokenResult:
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
            return TokenResult(
                cur.access_token, cur.id_token, cur.result
            )
        else:
            log.warning("Didnt match %s %s", got, cur.hashed)

        return None

    @classmethod
    def create(
            cls, username: str, password: str, token_result: TokenResult
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
