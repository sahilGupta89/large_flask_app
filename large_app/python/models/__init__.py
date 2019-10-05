from flask_apispec import FlaskApiSpec

from .alerts import AlertSubscription, AlertType
from .database import db
from .marshmallow import marshmallow
from .schemas import UserSchema
from .user import User, Auth0Mapping, BasicCache

docs = FlaskApiSpec()
__all__ = [
    "db",
    "docs",
    "marshmallow",
    "User",
    "UserSchema",
    "AlertSubscription",
    "AlertType",
    "Auth0Mapping",
    "BasicCache"
]
