import subprocess
from datetime import datetime
from pathlib import Path

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
        stacks = [
            DataStack(path.stem, path)
            for path in (self.workbench_path / "data-stacks/").glob("*")
            if path.name not in [".", ".."]
        ]
        stacks = [DataStack("0", self.workbench_path / "data-stacks/0")]
        return {d.id: d for d in stacks if d.path.exists()}

    @property
    def current_data_stack(self):
        if len(self.data_stacks) > 0:
            return self.data_stacks["0"]
        else:
            return None

    @classmethod
    def ensure_user(cls, email):
        u = User.query.filter(User.email == email).one_or_none()
        if u is None:
            u = User(email=email)
            db.session.add(u)
            db.session.commit()

        u.workbench_path.mkdir(parents=True, exist_ok=True)

        if len(u.data_stacks) == 0:
            DataStack.create_at(u.workbench_path / "data-stacks/0")

        return u


class DataStack:
    def __init__(self, id, path):
        self.id = id
        self.path = Path(path)

    @classmethod
    def create_at(cls, path):
        path = Path(path)
        run = path / "run"
        if not run.exists():
            if not path.exists():
                path.mkdir(parents=True)
            script = CONFIG.BE_BIN_DIR / "bootstrap-data-stack"
            subprocess.check_call([str(script)], cwd=path)

    @property
    def libds(self):
        return LibDS(self.path)
