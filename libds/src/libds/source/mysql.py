import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from pprint import pformat, pprint  # noqa: F401

import MySQLdb
from MySQLdb import _exceptions as exceptions
from MySQLdb.cursors import SSCursor

from libds.data_node import DataNode
from libds.model import data_type as dt
from libds.source import BaseSource, Record
from libds.utils import yaml_load


def _fetchone(cur, stmt, *args):
    cur.execute(stmt, *args)
    return cur.fetchone()[0]


def _fetchall(cur, stmt, *args):
    cur.execute(stmt, *args)
    return cur


def _quote_with(string, q_char):
    return q_char + string.replace(q_char, q_char + q_char) + q_char


def _column_spec_for_unpacking(
    column_name, data_type, is_nullable, numeric_precision, numeric_scale
):
    if data_type in ["varchar", "text"]:
        type = dt.Text()
    elif data_type in ["tinyint"]:
        type = dt.Integer(width=8)
    elif data_type in ["smallint"]:
        type = dt.Integer(width=16)
    elif data_type in ["mediumint", "int"]:
        type = dt.Integer(width=32)
    elif data_type in ["bigint"]:
        type = dt.Integer(width=64)
    elif data_type in ["decimal"]:
        type = dt.Decimal(precision=numeric_precision, scale=numeric_scale)
    elif data_type in ["float"]:
        type = dt.Float(width=32)
    elif data_type in ["double"]:
        type = dt.Float(width=64)

    type.is_nullable = is_nullable == "YES"

    return [column_name, type]


@dataclass
class SourceTable:
    table_name: str = None
    load: bool = None
    unpack: bool = None

    def info(self):
        return dict(load=self.load or False, unpack=self.unpack or False)


class MySQL(BaseSource):
    ALL_TABLES = ";-all-;"

    def __init__(self, **kwargs):
        self.connect_args = kwargs.pop("connect_args", {})
        tables = kwargs.pop("tables", None)
        if tables is None:
            self.tables = None
        else:
            self.tables = {}
            if isinstance(self.tables, list):
                for name in tables:
                    self.tables[name] = SourceTable(
                        table_name=name, load=True, unpack=True
                    )
            else:
                for name, spec in tables.items():
                    self.tables[name] = SourceTable(
                        table_name=name,
                        load=spec.get("load", False),
                        unpack=spec.get("unpack", False),
                    )
        self.target_schema = kwargs.pop("target_schema", None)
        if self.target_schema is None:
            self.target_schema = "public"
        self.target_table_name_prefix = kwargs.pop("target_table_name_prefix", None)
        if self.target_table_name_prefix is None:
            self.target_table_name_prefix = ""
        super().__init__(**kwargs)

    @classmethod
    def load_from_yaml(cls, data_stack, file):
        data = yaml_load(file)

        init_args = {}
        for (
            prop
        ) in "connect_args tables target_schema target_table_name_prefix".split():
            if prop in data:
                init_args[prop] = data[prop]

        return cls(**init_args)

    def info(self):
        return self._info(
            connect_args=self.connect_args,
            target_schema=self.target_schema,
            target_table_name_prefix=self.target_table_name_prefix,
            tables={v.table_name: v.info() for v in self.tables.values()},
        )

    def connect_args_for_mysql(self):
        args = dict(use_unicode=True, charset="utf8", cursorclass=SSCursor)

        if "port" in self.connect_args:
            args["port"] = int(self.connect_args["port"])

        if "host" in self.connect_args:
            args["host"] = self.connect_args["host"]

        if "password_var" in self.connect_args:
            args["passwd"] = os.environ.get(self.connect_args["password_var"])
        elif "password" in self.connect_args:
            args["passwd"] = self.connect_args["password"]

        if "username" in self.connect_args:
            args["user"] = self.connect_args["username"]

        if "database" in self.connect_args:
            args["db"] = self.connect_args["database"]

        return args

    def connect(self):
        return MySQLdb.connect(**self.connect_args_for_mysql())

    def select_tables(self, cur):
        tables = {}
        for t in _fetchall(
            cur,
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = database() ORDER BY ordinal_position",
        ):
            table_name, column_name = t
            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append(column_name)
        return tables

    def inspect(self):
        connect_args = self.connect_args.copy()
        if "password" in connect_args:
            connect_args["password"] = (
                "sha256:" + sha256(connect_args["password"].encode("utf-8")).hexdigest()
            )
        try:
            cur = self.connect().cursor()
        except exceptions.OperationalError as oe:
            if oe.args[0] == 2003:
                code = "could-not-connect"
            else:
                code = oe.__class__.__name__

            return dict(
                error={"code": code, "error": pformat(oe), "args": connect_args}
            )

        return dict(
            data=dict(
                database=_fetchone(cur, "SELECT database()"),
                tables=self.select_tables(cur),
            )
        )

    def table_spec(self):
        if self.tables == MySQL.ALL_TABLES:
            cur = self.connect().cursor()
            return {name: SourceTable() for name in self.select_tables(cur).keys()}
        elif self.tables is None:
            return {}
        else:
            return self.tables

    def load_table_raw(self, schema_name, table_name):
        cur = self.connect().cursor()
        column_names = _fetchall(
            cur,
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = database() ORDER BY ordinal_position",
            [table_name],
        )

        json_obj = []
        for (name,) in column_names:
            json_obj.append(_quote_with(name, '"'))
            json_obj.append(_quote_with(name, "`"))

        query = f"SELECT json_object({', '.join(json_obj)}) FROM {table_name}"

        def as_record(row):
            return Record(data_str=row[0], extracted_at=datetime.utcnow())

        return self.data_stack.store.load_raw_from_records(
            schema_name=schema_name,
            table_name=self.target_table_name_prefix + table_name + "_raw",
            records=(as_record(row) for row in _fetchall(cur, query)),
        )

    def load_table_unpacked(self, schema_name, table_name):
        cur = self.connect().cursor()
        cols = _fetchall(
            cur,
            "SELECT column_name, data_type, is_nullable, numeric_precision, numeric_scale FROM information_schema.columns WHERE table_name = %s AND table_schema = database() ORDER BY ordinal_position",
            [table_name],
        )
        columns = [_column_spec_for_unpacking(*col) for col in cols]
        column_names = [c[0] for c in columns]

        query = f"SELECT {','.join(column_names)} FROM {table_name}"

        def as_record(row):
            return Record(
                data={col: value for col, value in zip(column_names, row)},
                extracted_at=datetime.utcnow(),
            )

        self.data_stack.store.load_unpacked_from_records(
            schema_name=schema_name,
            table_name=self.target_table_name_prefix + table_name + "_raw",
            columns=columns,
            records=(as_record(row) for row in _fetchall(cur, query)),
        )

    def data_nodes(self):
        nodes = [
            MySQLDatabaseNode(
                mysql=self,
                stale_after=timedelta(hours=6),
            )
        ]
        for t in self.table_spec().values():
            if t.load:
                nodes.append(
                    MySQLRawTableNode(
                        mysql=self,
                        schema_name=self.target_schema,
                        table_name=t.table_name,
                    )
                )
        return nodes


class MySQLDatabaseNode(DataNode):
    def __init__(self, mysql, stale_after):
        connect_args = mysql.connect_args_for_mysql()
        details = " ".join(
            [
                k + "=" + str(connect_args[k])
                for k in "host port db".split()
                if connect_args.get(k)
            ]
        )
        super().__init__(
            id=mysql.fqid(), details=details, upstream=[], stale_after=stale_after
        )

    def refresh(self, orchestrator):
        return True


class MySQLRawTableNode(DataNode):
    def __init__(self, mysql, schema_name, table_name):
        super().__init__(
            id=schema_name + "." + table_name + "_raw", upstream=mysql.fqid()
        )
        self.schema_name = schema_name
        self.table_name = table_name
        self.mysql = mysql

    def refresh(self, orchestrator):
        spec = self.mysql.table_spec()[self.table_name]
        if spec.unpack:
            self.mysql.load_table_unpacked(self.schema_name, self.table_name)
        else:
            self.mysql.load_table_raw(self.schema_name, self.table_name)
