from datetime import datetime

import pygit2

from diaas.config import CONFIG
from diaas.db import db


def hashid_computed(column_name):
    return db.Computed(
        f"id_encode({column_name}, 'U69XD2b3YaIJe2plIN31', 1, 'abcdefghjkmnpqrstuwxyz1234567890')"
    )


class ModifiedAtMixin:
    created_at = db.Column(db.DateTime(), server_default=db.text("now()::timestamp"))
    modified_at = db.Column(
        db.DateTime(),
        server_default=db.text("now()::timestamp"),
        onupdate=datetime.utcnow,
    )


class User(db.Model, ModifiedAtMixin):
    uid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("uid"))

    email = db.Column(db.String(), unique=True)


class Warehouse(db.Model, ModifiedAtMixin):
    whid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("whid"))

    repo = db.Column(db.String(), nullable=False)


class Workbench(db.Model, ModifiedAtMixin):
    wbid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("wbid"))

    uid = db.Column(db.Integer(), db.ForeignKey("user.uid"), nullable=False)
    whid = db.Column(db.Integer(), db.ForeignKey("warehouse.whid"), nullable=False)
    branch = db.Column(db.String(), default="master", nullable=False)
