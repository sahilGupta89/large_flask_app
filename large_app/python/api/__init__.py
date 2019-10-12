from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, jsonify
from flask_migrate import Migrate
from jose.exceptions import JWTError
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from auth0 import AuthError
import env
import loggers
from models import db, docs, marshmallow
from . import user, login
from .auth import login_manager
from .swaggerui import API_URL, SWAGGER_URL, swaggerui_blueprint
import wait_for_db
import time

current_version = "v1"
prefix = "/api/{}".format(current_version)

migrate = Migrate(directory="./api/migrations")

spec = APISpec(
    title="Large app - APIv1",
    description="## Our API",
    version="v1",
    swagger="2.0",
    openapi_version="2.0",
    plugins=[MarshmallowPlugin()],
    securityDefinitions={
        "httpBasic": {
            "type": "basic",
            "description": (
                "Authorization providing access to the "
                "backend. Currently only standard Basic "
                "Authentication is supported"
            ),
        },
        "auth0": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": (
                "https://trueenergy.eu.auth0.com/authorize"
                "?audience=apiv2.auth0.do.trnrg.co"
            ),
        },
    },
)


def create_app():
    if env.SENTRY_API_DSN:
        sentry_sdk.init(
            dsn=env.SENTRY_API_DSN,
            integrations=[FlaskIntegration()],
            environment=env.SENTRY_ENVIRONMENT,
            release=env.VERSION,
            send_default_pii=True,
        )

    app = Flask(__name__)
    loggers.init_app(app)
    app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": env.PGDB_CONNECTION_STRING,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "APISPEC_SPEC": spec,
            "APISPEC_SWAGGER_UI_URL": None,
            "APISPEC_SWAGGER_URL": API_URL,
        }
    )
    db.init_app(app)
    marshmallow.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(user.blueprint, url_prefix=prefix)
    app.register_blueprint(login.blueprint, url_prefix=prefix)
    # app.register_blueprint(power.blueprint, url_prefix=prefix)
    # app.register_blueprint(feed.blueprint, url_prefix=prefix)
    # app.register_blueprint(car.blueprint, url_prefix=prefix)
    # app.register_blueprint(prices.blueprint, url_prefix=prefix)

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route("/")
    def index():
        links = []

        for rule in app.url_map.iter_rules():
            links.append(f"{rule.methods} {rule}")

        return jsonify(links)

    @app.route("/helloworld")
    def helloworld():
        return "Hello, world"

    @app.route("/healthcheck")
    def health():
        return "OK"

    @app.route("/version")
    def version():
        return jsonify(version=env.VERSION, api_version=current_version)

    docs.init_app(app)

    @app.errorhandler(AuthError)
    def handle_auth_error(ex):  # pragma: no cover
        app.logger.warning(
            "Returning Auth Error %r",
            ex,
            extra={
                "auth_error": getattr(ex, "error", {"message": "n/a"}),
                "status_code": getattr(ex, "status_code", "-1"),
            },
        )
        response = jsonify(ex.error)
        response.status_code = ex.status_code

        if ex.reauth:
            response.headers[
                "WWW-Authenticate"
            ] = 'Basic realm="Login required"'

        return response

    @app.errorhandler(JWTError)
    def handle_jwt_error(ex):  # pragma: no cover
        response = jsonify(dict(error=str(ex)))
        response.status_code = 400

        return response

    return app
