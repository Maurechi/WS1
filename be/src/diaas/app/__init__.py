import sentry_sdk
from flask import Flask
from flask_session import Session

from diaas.app.internal import internal_api
from diaas.app.utils import flask_json
from diaas.app.v1 import api_v1
from diaas.config import CONFIG
from diaas.db import alembic, db

if CONFIG.ENABLE_SENTRY:
    sentry_sdk.init(CONFIG.SENTRY_DSN, traces_sample_rate=1.0)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_v1, url_prefix="/api/1")
    app.register_blueprint(internal_api, url_prefix="/api/_")
    app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_ADD_STATUS"] = False
    app.config["ALEMBIC"] = dict(
        script_location=str(CONFIG.INSTALL_DIR / "be/migrations"),
        file_template="%%(year)d-%%(month).2d-%%(day).2d_%%(rev)s_%%(slug)s",
    )
    app.config["SECRET_KEY"] = CONFIG.SESSION_SECRET_KEY.encode("utf-8")
    flask_json.init_app(app)
    db.init_app(app)
    alembic.init_app(app)

    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    if CONFIG.SESSION_COOKIE_IS_SECURE:
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
    else:
        app.config["SESSION_COOKIE_SECURE"] = False
        app.config["SESSION_COOKIE_HTTPONLY"] = False

    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_SQLALCHEMY"] = db
    Session(app)

    return app
