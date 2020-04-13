from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/api/docs"  # URL for exposing Swagger UI
API_URL = "/swagger/"

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "layout": "BaseLayout",
        "deepLinking": "true",
    },  # Swagger UI config overrides
    # oauth_config={
    #     "clientId": "Zeu4TO3koxp6ubeebSMbgb0DRLbjLT69",
    #     "scopeSeparator": " ",
    #     "additionalQueryStringParams": {},
    # },
)
