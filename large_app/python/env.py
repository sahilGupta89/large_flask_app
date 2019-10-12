import os

database="devdb"
user="devuser"
host="localhost"
password="password"

VERSION = os.environ.get("VERSION", "n/a")
DB_CONNECTION_STRING = os.environ.get(
    "DB_CONNECTION_STRING", "mysql+pymysql://localhost:3306/dev"
)

PGDB_CONNECTION_STRING = os.environ.get(
    "PGDB_CONNECTION_STRING", "postgresql+psycopg2://devuser:password@localhost:5432/devdb"
)

JSON_LOGGING = os.environ.get("JSON_LOGGING", "false") in ("1", "true", "True")


# Auth0 settings
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "trueenergy.eu.auth0.com")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "apiv2.auth0.do.trnrg.co")
AUTH0_ZEAPI_AUDIENCE = os.environ.get("AUTH0_ZeAPI_AUDIENCE", "https://zeapi.trnrg.co")

AUTH0_ALGORITHMS = os.environ.get("AUTH0_ALGORITHMS", "RS256").split(",")
AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "Z1myKXcwci61mGKFZhsWXoQ5Lz3WMErv")
AUTH0_CLIENT_SECRET = os.environ.get(
    "AUTH0_CLIENT_SECRET",
    "dluLmsGrajvMcYGLZLqF_gPnpk-1yXVWO5Eugqgpwu5U6GSjc4bSnURz-R3ySVZu",
)
AUTH0_UP_CONNECTION_NAME = os.environ.get(
    "AUTH0_UP_CONNECTION_NAME", "Username-Password-Authentication"
)

# Sentry
SENTRY_ADMIN_DSN = os.environ.get("SENTRY_ADMIN_DSN")
SENTRY_API_DSN = os.environ.get("SENTRY_API_DSN")
SENTRY_ZEAPI_DSN = os.environ.get("SENTRY_ZEAPI_DSN")
SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT")
SENTRY_CHAMPAPI_DSN = os.environ.get("SENTRY_CHAMPAPI_DSN")
SENTRY_BMWAPI_DSN = os.environ.get("SENTRY_BMWAPI_DSN")
SENTRY_JAGAPI_DSN = os.environ.get("SENTRY_JAGAPI_DSN")
SENTRY_SMARTMEAPI_DSN = os.environ.get("SENTRY_SMARTMEAPI_DSN")

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

# FREQ
FREQ_DASHBOARD_URL = os.environ.get("FREQ_DASHBOARD_URL", "")
FREQ_DK1_DASHBOARD_URL = os.environ.get("FREQ_DK1_DASHBOARD_URL", "")
FCR_POOL_AREA = os.environ.get("FCR_POOL_AREA", "DK2")
FCR_PLAN_BACKOFF_MINUTES = int(os.environ.get("FCR_PLAN_BACKOFF_MINUTES", 10))


# FOR CHAMP Service
CHAMP_BASE = os.environ.get("CHAMP_BASE", "https://iapi.charge.space/v1/chargers/")


# BMW Auth
BMW_AUTH_BASE = os.environ.get(
    "BMW_AUTH_BASE", "https://customer.bmwgroup.com/gcdm/oauth/authenticate"
)
# JAG Auth
JAG_AUTH_BASE = os.environ.get(
    "JAG_AUTH_BASE", "https://jlp-ifas.wirelesscar.net/ifas/jlr/tokens"
)

LOG_CARAPI_STATUS_RESPONSES = os.environ.get(
    "LOG_CARAPI_STATUS_RESPONSES", "false"
) not in ("false", "0", "False")
