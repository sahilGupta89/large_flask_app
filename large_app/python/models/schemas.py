from marshmallow_sqlalchemy import TableSchema
from .marshmallow import marshmallow as ma
from .user import User, UserLocation
from .alerts import AlertSubscription, AlertType


class UserSchema(TableSchema):
    class Meta:
        table = User.__table__
        exclude = ("deleted", "created", "updated")
        strict = True

    alerts = ma.List(
        ma.Nested(
            "AlertSubscriptionSchema",
            only=["enabled", "channels", "name", "description"],
        ),
        default=[],
        attribute="alert_subscriptions",
        dump_only=True,
    )
    locations = ma.Nested(
        "UserLocationSchema", default=[], many=True, dump_only=True
    )
    email = ma.Email(required=True)
    id = ma.Integer(dump_only=True)


User.schema = UserSchema()


class TokenResultSchema(ma.Schema):
    token_type = ma.String()
    access_token = ma.String()
    id_token = ma.String()
    refresh_token = ma.String()
    expires_in = ma.Integer()
    scope = ma.Integer()


class SuggestSchema(ma.Schema):
    model = ma.Integer(description="Unique Model identifier", example=14)
    text = ma.String(example="Jeg vil gerne have XYZ")


class AlertTypeSchema(ma.ModelSchema):
    class Meta:
        model = AlertType


class AlertSubscriptionSchema(TableSchema):
    class Meta:
        table = AlertSubscription.__table__

    alert_type = ma.Nested(AlertTypeSchema, many=False)


class ForgotPassword(ma.Schema):
    email = ma.Email()


class LoginSchema (ma.Schema):
    auth_type= ma.String(required=True)
    username = ma.String(required=True)
    password = ma.String(required=True)
