from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, jsonify

import env
import loggers
from user_module.models import db, docs, marshmallow
from . import user
from .swaggerui import API_URL, SWAGGER_URL, swaggerui_blueprint

current_version = "v1"
prefix = "/api/{}".format(current_version)

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
        }
    },
)


def create_app():
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

    app.register_blueprint(user.blueprint, url_prefix=prefix)
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

    return app
