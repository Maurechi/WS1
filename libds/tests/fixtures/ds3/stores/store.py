import os

from libds.source.sqlite import SQLite

path = os.environ.get("STORE_PATH", ":memory:")
SQLite(path)
