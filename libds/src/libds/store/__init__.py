import datetime
import re
import runpy
import secrets
from decimal import Decimal

from libds.utils import yaml_load


class BaseStore:
    def __init__(self, data_stack=None, id=None, filename=None):
        from libds.data_stack import (
            CURRENT_DATA_STACK,
            CURRENT_FILENAME,
            LOCAL_STORES,
        )

        self.data_stack = data_stack or CURRENT_DATA_STACK.value
        self.filename = None
        self._id = id

        if filename is not None:
            self.filename = filename
        elif CURRENT_FILENAME.value is not None:
            self.filename = CURRENT_FILENAME.value

        LOCAL_STORES.append(self)

    @staticmethod
    def from_file(filename):
        from libds.data_stack import CURRENT_FILENAME

        filename = filename.resolve()
        CURRENT_FILENAME.value = filename

        if filename.suffix == ".py":
            runpy.run_path(filename)

        if filename.suffix == ".yaml":
            spec = yaml_load(filename)
            if spec["type"] == "libds.store.sqlite.SQLite":
                from libds.store.sqlite import SQLite

                return SQLite.from_yaml(spec)
            if spec["type"] == "libds.store.clickhouse.ClickHouse":
                from libds.store.clickhouse import ClickHouse

                return ClickHouse.from_yaml(spec)
            else:
                raise ValueError(
                    f"Don't know how to build store of type {spec['type']} from {filename}"
                )

    @property
    def type(self):
        return self.__class__.__module__ + "." + self.__class__.__name__

    @property
    def id(self):
        if self._id is not None:
            return self._id
        elif self.filename is not None:
            return self.filename.stem
        else:
            return None

    def _info(self, **data):
        defaults = dict(
            type=self.type,
            id=self.id,
        )
        return {**defaults, **data}

    def info(self):
        return self._info()

    def execute(self, store):
        raise NotImplementedError()

    def model_id_to_table_name(self, model_id):
        return model_id

    def _cleanup_tables(self, p, schema_name, table_name):
        working = self.drop_tables_by_tag(schema_name, table_name, "working")
        p.display(f"Cleaned up working tables: {working}")
        tombstone = self.drop_tables_by_tag(schema_name, table_name, "tombstone")
        p.display(f"Cleaned up tombstone tables: {tombstone}")


def to_sample_value(value):
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    elif isinstance(value, (bool, int, str, type(None), float)):
        return value
    else:
        raise ValueError(f"Don't know how to make a sample datum from {value}.")


class BaseTable:
    def __init__(self, store, schema_name, table_name):
        self.store = store
        self.schema_name = schema_name
        self.table_name = table_name

    def sample(self, limit=None, order_by=None, where=None):
        if limit is None:
            limit = 23
        return self._sample(limit, order_by, where)


def with_random_suffix(table_name, tag=""):
    return "_".join(
        [
            table_name,
            tag,
            datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S"),
            secrets.token_hex(4),
        ]
    )


def random_suffix_regexp(table_name, tag=""):
    return re.compile(
        "_".join(
            [
                re.escape(table_name),
                re.escape(tag),
                "[0-9]{8}T[0-9]{6}",
                "[a-f0-9]{8}",
            ]
        )
    )
