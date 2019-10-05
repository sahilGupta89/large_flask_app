from flask import request
from flask_apispec import marshal_with, MethodResource, use_kwargs
from flask_login import current_user, login_required

# from auth0 import AuthError, management_api
from models import db, User
from models.schemas import UserSchema
from ..spec import docer, not_implemented


doc = docer("user")


class UserResource(MethodResource):
    @login_required
    @marshal_with(UserSchema, code=200, description="A user")
    @doc(description="Get the current logged in user", stub=False)
    def get(self):
        user = User.query.get(current_user.id)

        return user

    @use_kwargs(UserSchema)
    # @marshal_with(
    #     IdResultSchema, code=200, description="The id of the created user"
    # )
    @marshal_with(None, code=409, description="User already exists")
    @marshal_with(None, code=429, description="Too many requests")
    @marshal_with(
        None,
        code=400,
        description=(
            "Invalid input (missing user/pw in Authorization header,"
            " weak password etc)"
        ),
    )
    @doc(
        description=(
            "Create a new user - username and password should be in the "
            "Authorization header and the username should be equal to the "
            "email parameter"
        ),
        login_required=False,
        stub=False,
    )
    def post(self, **kwargs):
        user = User(**kwargs)

        # if user.exists():
        #     raise AuthError(
        #         error={
        #             "message": "User already exists",
        #             "error": "BadRequest",
        #         },
        #         status_code=409,
        #     )
        #
        # rauth = request.authorization
        #
        # if not rauth:
        #     raise AuthError(
        #         error={
        #             "message": (
        #                 "missing username/password basic Authorization "
        #                 "http header"
        #             ),
        #             "error": "BadRequest",
        #         },
        #         status_code=400,
        #     )
        #
        # username = rauth["username"]
        # password = rauth["password"]
        #
        # if username != user.email:
        #     raise AuthError(
        #         error={
        #             "message": "Username and email must be the same",
        #             "error": "BadRequest",
        #         },
        #         status_code=400,
        #     )
        # auth0_user = management_api.create_user(user, password)
        # user.add_mapping(auth0_user["user_id"])
        with db as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        return user

    @login_required
    @use_kwargs(UserSchema)
    @marshal_with(None, code=204, description="OK")
    @doc(description="Update user details")
    @not_implemented
    def put(self, **kwargs):
        return "", 204
