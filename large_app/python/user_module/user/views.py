from flask import Blueprint
from user_module.models import docs
from .user_resource import UserResource


blueprint = Blueprint("user", __name__)

blueprint.add_url_rule("/user", view_func=UserResource.as_view("user"))
docs.register(UserResource, endpoint="user", blueprint=blueprint.name)

__all__ = ["blueprint"]