import subprocess
from uuid import uuid4
from datetime import datetime

from diaas.config import CONFIG
from diaas.db import db


# NOTE To make this work the first migration will need
# op.execute("CREATE EXTENSION pg_hashids;") op.execute("DROP
# EXTENSION pg_hashids") 20201222:mb
def hashid_computed(column_name):
    return db.Computed(
        f"id_encode({column_name}, '{CONFIG.PG_HASHIDS_SALT}', 1, 'abcdefghjkmnpqrstuwxyz1234567890')"
    )


class ModifiedAtMixin:
    created_at = db.Column(db.DateTime(), server_default=db.text("now()::timestamp"))
    modified_at = db.Column(
        db.DateTime(),
        server_default=db.text("now()::timestamp"),
        onupdate=datetime.utcnow,
    )


class DataStack(db.Model, ModifiedAtMixin):
    dsid = db.Column(db.String(), primary_key=True)

    users = db.relationship("User", secondary="user_data_stack")

    @property
    def directory(self):
        return CONFIG.DS_STORE / self.dsid


class UserDataStack(db.Model):
    dsid = db.Column(db.String(), db.ForeignKey("data_stack.dsid"))
    uid = db.Column(db.Integer(), db.ForeignKey("user.uid"))
    __table_args__ = (db.PrimaryKeyConstraint(dsid, uid), {})


class User(db.Model, ModifiedAtMixin):
    # Bump this up to something nice with op.execute("ALTER SEQUENCE
    # user_uid_seq RESTART WITH 1000 START WITH 1000 MINVALUE 1000;")
    # in the migration.

    uid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("uid"))

    email = db.Column(db.String(), unique=True)

    data_stacks = db.relationship("DataStack", secondary="user_data_stack", back_populates="users")

    @property
    def display_name(self):
        email_parts = self.email.split("@")
        return email_parts[0].lower()

    @classmethod
    def ensure_user(cls, email):
        u = User.query.filter(User.email == email).one_or_none()
        if u is None:
            u = User(email=email)
            db.session.add(u)
            db.session.commit()

        if len(u.data_stacks) == 0:
            ds = DataStack(dsid=str(uuid4()))
            u.data_stacks.append(ds)
            db.session.add(ds)
            db.session.commit()
            subprocess.check_call(["dss", "init", str(ds.directory)])

        db.session.commit()
        return u
