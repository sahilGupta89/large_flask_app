from flask_apispec import marshal_with, MethodResource, use_kwargs
from flask_login import login_required

from models.schemas import AlertSubscriptionSchema
from ..spec import docer, empty_204, not_implemented


doc = docer("user")


class UserAlertsResource(MethodResource):
    @doc(description="Update a location for this user")
    @marshal_with(None, 204, description="Location changed OK")
    @not_implemented
    @login_required
    @use_kwargs(AlertSubscriptionSchema(many=True))
    def put(self, id, **kwargs):
        return empty_204()
