from flask import Blueprint, request
from flask_apispec import marshal_with, MethodResource, use_kwargs
from models.schemas import TokenResultSchema, ForgotPassword, LoginSchema
from models import docs
from ..auth import basic_auth, token_auth, unauth
from ..spec import docer, empty_204, not_implemented

blueprint = Blueprint("login", __name__)

doc = docer("login")


class LoginResource(MethodResource):
    @marshal_with(
        TokenResultSchema,
        code=200,
        description=(
            "When using basic auth, this returns the token information related"
            " to this login"
        ),
    )
    @marshal_with(None, 204, description="When using token. Token OK")
    @doc(description="Perform login - and potentially get a token", stub=False)
    def get(self):
        basic_auth_result = basic_auth.request_to_auth_result(request)

        if basic_auth_result:
            return basic_auth_result.token_result.result
        elif token_auth.user_from_access_token(request):
            return empty_204()
        else:
            return unauth()

    @use_kwargs(LoginSchema)
    @doc(
        description=(
            "Change username (email) and/or password (all fields are required)"
        )
    )
    @marshal_with(None, 204, description="OK")
    @not_implemented
    def put(self, **kwargs):
        return empty_204()

    @use_kwargs(ForgotPassword)
    @marshal_with(None, 204, description="OK")
    @doc(
        description="Get new password (forgot password)", login_required=False
    )
    @not_implemented
    def post(self, **kwargs):
        return empty_204()


blueprint.add_url_rule("/login", view_func=LoginResource.as_view("login"))


docs.register(LoginResource, endpoint="login", blueprint=blueprint.name)


__all__ = ["blueprint"]
