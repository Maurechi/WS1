import os

from libds.src.sqlite import SQLite

path = os.environ.get("STORE_PATH", ":memory:")
SQLite(path)
