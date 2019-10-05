from flask import Blueprint
from flask_apispec import marshal_with, use_kwargs
from flask_login import login_required

from models import docs
from models.schemas import SuggestSchema
from .user_alerts import UserAlertsResource
# from .user_location import UserLocationResource
# from .user_locations import UserLocationsResource
from .user_resource import UserResource
from ..spec import docer, empty_204, not_implemented

doc = docer("user")


blueprint = Blueprint("user", __name__)
blueprint.add_url_rule("/user", view_func=UserResource.as_view("user"))
# blueprint.add_url_rule(
#     "/user/locations",
#     view_func=UserLocationsResource.as_view("user_locations"),
# )
# blueprint.add_url_rule(
#     "/user/location/<int:id>",
#     view_func=UserLocationResource.as_view("user_location"),
# )
blueprint.add_url_rule(
    "/user/alerts", view_func=UserAlertsResource.as_view("user_alerts")
)


@blueprint.route("/user/suggest", methods=["POST"])
@doc(
    description=(
        "An authorised user can vote for an comment on a EV model that is not "
        "currently supported."
    )
)
@not_implemented
@use_kwargs(SuggestSchema)
@marshal_with(None, code=204)
@login_required
def suggest():
    return empty_204()


# docs.register(UserResource, endpoint="user", blueprint=blueprint.name)
# docs.register(
#     UserLocationsResource, endpoint="user_locations", blueprint=blueprint.name
# )
# docs.register(
#     UserLocationResource, endpoint="user_location", blueprint=blueprint.name
# )
docs.register(
    UserAlertsResource, endpoint="user_alerts", blueprint=blueprint.name
)

docs.register(suggest, blueprint=blueprint.name)


__all__ = ["blueprint"]
