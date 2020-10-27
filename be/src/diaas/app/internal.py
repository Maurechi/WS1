import os
from pprint import pformat
import traceback
import psycopg2
import logging
from flask import Blueprint, request
from diaas.app.utils import NotFoundError, as_json
from diaas.config import CONFIG
import alembic


internal_api = Blueprint("internal_api", __name__, static_folder=None)

log = logging.getLogger(__name__)


@internal_api.route(
    "/", defaults={"path": "/"}, methods=["GET", "POST", "PUT", "DELETE"]
)
@internal_api.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def not_found(path):
    raise NotFoundError("route", request.url)


@internal_api.route("/upgrade", methods=["POST"])
@as_json
def alembic_migrate():
    revisions = []

    have_work = [True]
    while have_work[0]:

        def do_upgrade(revision, context):
            missing = alembic.script_directory._upgrade_revs("heads", revision)
            if missing:
                revisions.append(missing[0])
                return [missing[0]]
            else:
                have_work[0] = False
                return []

        alembic.run_migrations(do_upgrade)

    def _as_json(r):
        return {
            "doc": r.doc,
            "revision": r.revision.revision,
            "name": r.name,
            "next": r.revision.nextrev,
        }

    return {"revisions": [_as_json(r) for r in revisions]}, 200


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

    heads = [] # alembic.heads()

    return {
        "ok": True,
        "user": row[0],
        "name": row[1],
        "version": row[2],
        "heads": pformat(heads),
    }


def _runtime_info():
    runtime = {}

    runtime["config"] = CONFIG.data
    runtime["env"] = os.environ.copy()

    return runtime


@internal_api.route("/health")
@as_json
def health():
    health = {}

    token = request.args.get("token")

    app = _app_health()
    db = _db_health()

    health["ok"] = app["ok"] and db["ok"]

    if token == CONFIG.INTERNAL_API_TOKEN:
        health["app"] = app
        health["database"] = db
        health["runtime"] = _runtime_info()

    return (
        health,
        200 if health["ok"] else 503,
    )
