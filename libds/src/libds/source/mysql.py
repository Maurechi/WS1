from hashlib import sha256
from pprint import pformat, pprint  # noqa: F401

import MySQLdb
from MySQLdb import _exceptions as exceptions
from MySQLdb.cursors import SSCursor

from libds.data_node import DataNode
from libds.source import BaseSource, Record


def _fetchone(cur, stmt, *args):
    cur.execute(stmt, *args)
    return cur.fetchone()[0]


def _fetchall(cur, stmt, *args):
    cur.execute(stmt, *args)
    return cur


def _quote_with(string, q_char):
    return q_char + string.replace(q_char, q_char + q_char) + q_char


class MySQL(BaseSource):
    ALL_TABLES = ";-all-;"

    def __init__(self, **kwargs):
        self.connect_args = kwargs.pop("connect_args", {})
        self.tables = kwargs.pop("tables", None)
        if isinstance(self.tables, list):
            self.tables = {table_name: {} for table_name in self.tables}
        self.target_schema = kwargs.pop("target_schema", "public")
        self.target_table_name_prefix = kwargs.pop("target_table_name_prefix", None)
        super().__init__(**kwargs)

    def info(self):
        return self._info(
            connect_args=self.connect_args,
            target_schema=self.target_schema,
            target_table_name_prefix=self.target_table_name_prefix,
            tables=self.tables,
        )

    def connect_args_for_mysql(self):
        connect_args = dict(use_unicode=True, charset="utf8", cursorclass=SSCursor)

        if "port" in self.connect_args:
            connect_args["port"] = int(self.connect_args["port"])
        mapping = {
            "host": "host",
            "username": "user",
            "password": "passwd",
            "database": "db",
        }
        for frm, to in mapping.items():
            if frm in self.connect_args:
                value = self.connect_args[frm]
                if value is not None:
                    connect_args[to] = value

        return connect_args

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
                code = "con-not-connect"
            else:
                code = oe.__class__.__name__

            return dict(
                {"error": {"code": code, "error": pformat(oe), "args": connect_args}}
            )

        return dict(
            data=dict(
                conn=connect_args,
                database=_fetchone(cur, "SELECT database()"),
                tables_available=self.select_tables(cur),
                tables=self.tables,
            )
        )

    def table_spec(self):
        if self.tables == MySQL.ALL_TABLES:
            cur = self.connect().cursor()
            return {name: {} for name in self.select_tables(cur).keys()}
        else:
            return self.tables

    def load(self, reload=False):
        tables = self.table_spec()
        # NOTE do this sort so we always process the tables in the
        # same order, not needed but convenient for the caller
        # 20210310:mb
        for table_name in sorted(tables.keys()):
            self.load_one_table(table_name, tables[table_name], reload)
        return []

    def load_one_table(self, table_name, spec, reload):
        store = self.data_stack.store
        if spec is None:
            spec = {}
        schema_name = self.target_schema
        if self.target_table_name_prefix is not None:
            table_name = self.target_table_name_prefix + table_name

        if reload:
            store.truncate_raw_table(schema_name, table_name)

        cur = self.connect().cursor()
        column_names = _fetchall(
            cur,
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = database() ORDER BY ordinal_position",
            [table_name],
        )

        json_obj = []
        for (name,) in column_names:
            if "exclude" in spec:
                if name in spec["exclude"]:
                    continue
            if "include" in spec:
                if name not in spec["include"]:
                    continue
            json_obj.append(_quote_with(name, '"'))
            json_obj.append(_quote_with(name, "`"))

        primary_key_expr = spec.get("primary_key", "NULL")
        valid_at_expr = spec.get("valid_at", "NULL")

        most_recent_raw_timestamp = store.most_recent_raw_timestamp(
            schema_name, table_name
        )
        query = f"SELECT json_object({', '.join(json_obj)}), cast({primary_key_expr} as char), {valid_at_expr} FROM {table_name}"
        query_args = []
        if most_recent_raw_timestamp is not None:
            query += " WHERE {valid_at_expr} > %s"
            query_args = [most_recent_raw_timestamp]

        def as_record(row):
            return Record(data_str=row[0], primary_key=row[1], valid_at=row[2])

        return self.data_stack.store.append_raw(
            schema_name=schema_name,
            table_name=table_name,
            records=(as_record(row) for row in _fetchall(cur, query, query_args)),
        )

    def register_data_nodes(self, data_stack):
        fqid = self.fqid()
        details = " ".join(
            [k + "=" + str(v) for k, v in self.connect_args_for_mysql().items()]
        )
        data_stack.register_data_nodes(
            DataNode(
                id=fqid,
                inputs=[],
                details=details,
            )
        )
        for table_name in self.table_spec().keys():
            data_stack.register_data_nodes(
                DataNode(
                    id=self.target_schema + "." + table_name + "_raw",
                    inputs=[fqid],
                )
            )
