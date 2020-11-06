import os
from pathlib import Path


class Config:
    def __init__(self):
        self.data = dict()
        self.configurable("BEDB_PGDATABASE")
        self.configurable("BEDB_PGHOST")
        self.configurable("BEDB_PGPASSWORD")
        self.configurable("BEDB_PGPORT", type=int)
        self.configurable("BEDB_PGUSER")
        self.configurable("BEDB_PGDATABASE")
        self.configurable("DEPLOYMENT_COMMIT_REF_NAME")
        self.configurable("DEPLOYMENT_COMMIT_SHA")
        self.configurable("DEPLOYMENT_COMMIT_TITLE")
        self.configurable("DEPLOYMENT_ENVIRONMENT")
        self.configurable("INTERNAL_API_TOKEN")
        self.configurable("SESSION_STORE_DIR", type=Path)
        self.configurable("INSTALL_DIR", type=Path)
        self.configurable("SESSION_SECRET_KEY")

        self.configurable("ENABLE_SENTRY", type=bool)
        if self.ENABLE_SENTRY:
            self.configurable("SENTRY_DSN")

    def configurable(self, key, type=str):
        if type is Path:
            transform = lambda v: Path(v.rstrip("/"))  # noqa: E731
        elif type is str:
            transform = lambda v: v  # noqa: E731
        elif type is int:
            transform = lambda v: int(v)  # noqa: E731
        elif type is bool:
            transform = lambda v: v.lower() in ["yes", "1", "true", "on"]  # noqa: E731

        v = os.environ.get(f"DIAAS_{key}", None)
        if v is None:
            raise ValueError(f"Missing required config variable {key}")
        else:
            value = transform(v)

        self.data[key] = value

    def __getattr__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            raise ValueError(f"Unknown config setting {key}")

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        schema = "postgresql+psycopg2"
        credentials = f"{self.BEDB_PGUSER}:{self.BEDB_PGPASSWORD}"
        dbname = self.BEDB_PGDATABASE
        args = f"host={self.BEDB_PGHOST}&port={self.BEDB_PGPORT}"
        return f"{schema}://{credentials}@/{dbname}?{args}"

    def session_dir(self, session_id):
        return Path(self.SESSION_STORE_DIR) / session_id


CONFIG = Config()
