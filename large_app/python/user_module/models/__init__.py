from flask_apispec import FlaskApiSpec
from .database import db
from .marshmallow import marshmallow
from .user import User, BasicCache
from .schemas import UserSchema

docs = FlaskApiSpec()
__all__ = [
    "db",
    "docs",
    "marshmallow",
    "User",
    "UserSchema",
    "BasicCache"
]