import subprocess
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pygit2

from diaas.config import CONFIG
from diaas.db import db
from diaas.libds import LibDS


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


class User(db.Model, ModifiedAtMixin):
    # Bump this up to something nice with op.execute("ALTER SEQUENCE
    # user_uid_seq RESTART WITH 1000 START WITH 1000 MINVALUE 1000;")
    # in the migration.

    uid = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("uid"))

    email = db.Column(db.String(), unique=True)

    @property
    def display_name(self):
        email_parts = self.email.split("@")
        return email_parts[0].lower()

    @property
    def workbench_path(self):
        return (CONFIG.WORKBENCH_STORE / self.code).resolve()

    @property
    def data_stacks(self):
        return [
            DataStack(path)
            for path in (self.workbench_path / "data-stacks/").glob("*")
            if path.name not in [".", ".."]
        ]

    @classmethod
    def ensure_user(cls, email):
        u = User.query.filter(User.email == email).one_or_none()
        if u is None:
            u = User(email=email)
            db.session.add(u)
            db.session.commit()

        u.workbench_path.mkdir(parents=True, exist_ok=True)

        if len(u.data_stacks) == 0:
            origin_dir = CONFIG.DS_STORE / str(uuid4())
            DataStack.create_origin(origin_dir)
            u.clone_data_stack(origin_dir)

        return u

    def clone_data_stack(self, origin):
        index = len(self.data_stacks)
        pygit2.clone_repository(
            url=origin, path=str(self.workbench_path / "data-stacks" / str(index))
        )


class DataStack:
    def __init__(self, path):
        self.path = Path(path)

    @classmethod
    def create_origin(cls, path):
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True)
        script = CONFIG.INSTALL_DIR / "be/bin/bootstrap-data-stack"
        subprocess.check_call([str(script)], cwd=path)

    @property
    def libds(self):
        return LibDS(self.path)
