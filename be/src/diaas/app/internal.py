import logging
import os
import traceback
from pprint import pformat

import psycopg2
from flask import Blueprint, request

from diaas.app.utils import NotFoundError, as_json
from diaas.config import CONFIG

internal_api = Blueprint("internal_api", __name__, static_folder=None)

log = logging.getLogger(__name__)


@internal_api.route(
    "/", defaults={"path": "/"}, methods=["GET", "POST", "PUT", "DELETE"]
)
@internal_api.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def not_found(path):
    raise NotFoundError("route", request.url)


def _app_health():
    health = {
        "ok": True,
        "commit": {
            "sha": CONFIG.DEPLOYMENT_COMMIT_SHA,
            "title": CONFIG.DEPLOYMENT_COMMIT_TITLE,
            "ref": CONFIG.DEPLOYMENT_COMMIT_REF_NAME,
        },
    }
    return health


def _db_health():
    try:
        options = dict(
            user=CONFIG.BEDB_PGUSER,
            dbname=CONFIG.BEDB_PGDATABASE,
            password=CONFIG.BEDB_PGPASSWORD,
            host=CONFIG.BEDB_PGHOST,
            port=CONFIG.BEDB_PGPORT,
        )
        parts = [f"{key}={value}" for key, value in options.items()]
        connection_string = " ".join(parts)
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute("SELECT current_user, current_database(), version();")
        res = cur.fetchall()
    except Exception:
        return {"ok": False, "data": traceback.format_exc()}

    if len(res) != 1:
        return {"ok": False, "data": pformat(res)}
    row = res[0]
    if len(row) != 3:
        return {"ok": False, "data": pformat(res)}

    heads = []  # alembic.heads()

    return {
        "ok": True,
        "user": row[0],
        "name": row[1],
        "version": row[2],
        "heads": pformat(heads),
    }


def _runtime_info():
    return


@internal_api.route("/health")
@as_json
def health():
    app = _app_health()
    db = _db_health()

    health = dict(ok=app["ok"] and db["ok"])

    token = request.args.get("token")
    if token == CONFIG.INTERNAL_API_TOKEN:
        health["app"] = app
        health["database"] = db
        health["runtime"] = dict(confg=CONFIG.data, env=os.environ.copy())

    return (
        health,
        200 if health["ok"] else 503,
    )


@internal_api.route("/echo")
@as_json
def echo():
    return dict(ok=True)
