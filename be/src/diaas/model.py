from datetime import datetime

import pygit2

from diaas.config import CONFIG
from diaas.db import db


def hashid_computed(column_name):
    return db.Computed(
        f"id_encode({column_name}, 'U69XD2b3YaIJe2plIN31', 1, 'abcdefghjkmnpqrstuwxyz1234567890')"
    )


class User(db.Model):
    uid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("id"))
    email = db.Column(db.String(), unique=True)


class Warehouse(db.Model):
    whid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("id"))
    repo = db.Column(db.String(), nullable=False)


class Workbench(db.Model):
    wbid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("id"))
    uid = db.Column(db.Integer(), db.ForeignKey("user.uid"), nullable=False)
    whid = db.Column(db.Integer(), db.ForeignKey("warehouse.whid"), nullable=False)
    branch = db.Column(db.String(), default="master", nullable=False)

    first_created = db.Column(db.DateTime(), server_default=db.text("now()::timestamp"))
    last_modified = db.Column(
        db.DateTime(),
        server_default=db.text("now()::timestamp"),
        onupdate=datetime.utcnow,
    )

    def create_local_data(self, local_dir):
        local_dir.mkdir(parents=True, exist_ok=True)
        project_checkout = local_dir / "project"
        project_checkout.mkdir()
        pygit2.init_repository(project_checkout, bare=False)

    def ensure_local_data(self):
        local_dir = CONFIG.session_dir(self.code)
        if not local_dir.exists():
            self.create_local_data(local_dir)
        return local_dir
