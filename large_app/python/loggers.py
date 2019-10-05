from datetime import datetime
import json
import logging
import os

from pythonjsonlogger import jsonlogger


def deny_healthcheck_filter(record):

    return (
        "/health" not in record.msg
        and "/health" not in getattr(record, "message", "")
        and (
            "get" not in dir(getattr(record, "args", {}))
            or "/health" not in getattr(record, "args", {}).get("r", "")
        )
    )


class NoHealthcheck:
    def filter(self, record):
        return deny_healthcheck_filter(record)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(
            log_record, record, message_dict
        )
        # print(log_record, record, message_dict)

        if log_record.get("name", "") == "gunicorn.access":
            log_record.update(json.loads(log_record.get("message", "{}")))
            log_record["message"] = "{request_method} {request_path}".format(
                **log_record
            )

        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = log_record.pop("asctime", None)

            if not now:
                now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname

        for p in ["levelname"]:
            log_record.pop(p, None)


def init_app(app):
    if app.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format=(
                "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} "
                "%(levelname)s - %(message)s"
            ),
        )
        logging.getLogger("watchdog.observers").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").propagate = False

        if os.environ.get("NO_SQL_LOGGING"):
            logging.getLogger("sqlalchemy.engine.base").setLevel(
                logging.WARNING
            )
        else:
            logging.getLogger("sqlalchemy.engine.base").setLevel(logging.INFO)
    app.logger.setLevel(logging.DEBUG)
    from flask.logging import default_handler

    app.logger.removeHandler(default_handler)
