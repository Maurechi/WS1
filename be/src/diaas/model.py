from datetime import datetime

import pygit2
import sqlalchemy.types as types

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

    workbenches = db.relationship(
        "Workbench", back_populates="user", cascade="all,delete-orphan"
    )


class Warehouse(db.Model, ModifiedAtMixin):
    whid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("whid"))

    repo = db.Column(db.String(), nullable=False)

    workbenches = db.relationship(
        "Workbench", back_populates="warehouse", cascade="all,delete-orphan"
    )


class Workbench(db.Model, ModifiedAtMixin):
    wbid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("wbid"))

    uid = db.Column(
        db.Integer(), db.ForeignKey("user.uid", ondelete="cascade"), nullable=False
    )
    user = db.relationship("User", back_populates="workbenches")

    whid = db.Column(
        db.Integer(),
        db.ForeignKey("warehouse.whid", ondelete="cascade"),
        nullable=False,
    )
    warehouse = db.relationship("Warehouse", back_populates="workbenches")

    branch = db.Column(db.String(), default="master", nullable=False)


def initial_user_setup(email):
    wh = Warehouse(repo="/dev/null")
    db.session.add(wh)
    db.session.commit()
    # NOTE the code is generated in the db (maybe that was a mistake?)
    # so we need to commit and load it here 20201108:mb
    repo_dir = str(CONFIG.FILE_STORE / "warehouse" / wh.code / "repo")
    pygit2.init_repository(repo_dir)
    wh.repo = repo_dir
    u = User(email=email)
    wb = Workbench(user=u, warehouse=wh, branch="master")
    db.session.add(wh)
    db.session.add(u)
    db.session.add(wb)
    db.session.commit()
    return u
