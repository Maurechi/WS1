from diaas.config import CONFIG
from datetime import datetime
from diaas.db import db


def hashid_computed(column_name):
    return db.Computed(f"id_encode({column_name}, 'U69XD2b3YaIJe2plIN31', 1, 'abcdefghjkmnpqrstuwxyz1234567890')")


class Session(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("id"))
    first_created = db.Column(db.DateTime(), server_default=db.text("now()::timestamp"))
    last_modified = db.Column(db.DateTime(), server_default=db.text("now()::timestamp"), onupdate=datetime.utcnow)

    def create_local_data(self, local_dir):
        local_dir.mkdir(parents=True, exist_ok=True)

    def ensure_local_data(self):
        local_dir = CONFIG.session_dir(self.code)
        if not local_dir.exists():
            self.create_local_data()
        return local_dir


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(), hashid_computed("id"))
