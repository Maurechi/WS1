from pprint import pformat

import clickhouse_driver.errors
from clickhouse_driver import Client

from libds.model import data_type
from libds.store import (
    BaseStore,
    BaseTable,
    to_sample_value,
    with_random_suffix,
)
from libds.store.clickhouse_error_codes import ERROR_CODES
from libds.utils import DSException, GaugeProgress, InsertProgress


def _data_type_to_clickhouse_type(t):
    if isinstance(t, data_type.Text):
        type_string = "String"
    elif isinstance(t, data_type.Integer):
        if t.width <= 8:
            type_string = "Int8"
        elif t.width <= 16:
            type_string = "Int16"
        elif t.width <= 32:
            type_string = "Int32"
        elif t.width <= 64:
            type_string = "Int64"
        elif t.width <= 128:
            type_string = "Int128"
        elif t.width <= 256:
            type_string = "Int256"
        else:
            raise ValueError(f"Int width {t.width} is too wide for clickhouse.")
    elif isinstance(t, data_type.Float):
        if t.width <= 32:
            type_string = "Float32"
        elif t.width <= 64:
            type_string = "Float64"
        else:
            raise ValueError(f"Float width {t.width} is too wide for clickhouse.")
    elif isinstance(t, data_type.Decimal):
        p, s = (t.precision, t.scale)
        if p > 76:
            raise ValueError(f"Decimal precision {p} is too wide for clickhouse.")
        if s > p:
            raise ValueError(
                f"Decimal scale {s} is greater than requested precision {p}."
            )
        type_string = f"Decimal({p}, {s})"
    else:
        raise ValueError("No matching clickhouse type for {t}")
    if t.is_nullable:
        type_string = f"Nullable({type_string})"
    return type_string


class ClickHouseServerException(DSException):
    def __init__(self, se=None, source=None):
        self.se = se
        self.source = source

    def as_json(self):

        if self.se is None:
            details = "-no se object-"
        else:
            se = self.se
            error_name = ERROR_CODES.get(se.code, None)
            if error_name is None:
                error = str(se.code)
            else:
                error = f"{error_name}({se.code})"
            details = f"{error}:\n{se.message}"

        return dict(
            code=self.code(),
            details=details,
            source=self.source,
        )

    def __str__(self):
        return (
            "<"
            + self.__class__.__name__
            + " "
            + " ".join(["=".join(item) for item in self.as_json().items()])
            + ">"
        )


def _clickhouse_server_exception(se, query, params):
    source = query
    if params:
        source += "(" + pformat(params) + ")"
    else:
        source = query
    return ClickHouseServerException(se=se, source=source)


class ClickHouseClient:
    def __init__(self, **kwargs):
        self.client = Client(**kwargs)

    def execute(self, query, params=None, **kwargs):
        # print(f"Executing `{stmt}`")
        try:
            return self.client.execute(query, params=params, **kwargs)
        except clickhouse_driver.errors.ServerException as se:
            raise _clickhouse_server_exception(se, query, params)

    def execute_with_progress(self, query, params=None, **kwargs):
        try:
            return self.client.execute_with_progress(query, params=params, **kwargs)
        except clickhouse_driver.errors.ServerException as se:
            raise _clickhouse_server_exception(se, query, params)

    def execute_iter(self, query, params=None, *args, **kwargs):
        try:
            return self.client.execute_iter(query, params=params, **kwargs)
        except clickhouse_driver.errors.ServerException as se:
            raise _clickhouse_server_exception(se, query, params)

    def table_exists(self, schema_name, table_name):
        res = self.execute(
            "select count(*) as c from system.tables where database = %(schema_name)s and name = %(table_name)s",
            dict(schema_name=schema_name, table_name=table_name),
        )
        return res[0][0] > 0


class ClickHouse(BaseStore):
    def __init__(self, port=None, host=None):
        self.parameters = dict(port=9000, host="localhost")
        if port is not None:
            self.parameters["port"] = port
        if host is not None:
            self.parameters["host"] = host
        super().__init__()

    @classmethod
    def from_yaml(cls, yaml):
        return cls(port=yaml["port"], host=yaml["host"])

    def info(self):
        return self._info(parameters=self.parameters)

    def client(self, schema_name="public"):
        return ClickHouseClient(
            host=self.parameters["host"],
            port=self.parameters["port"],
            database=schema_name,
        )

    def _ensure_schema(self, schema_name):
        default = self.client(schema_name="default")
        default.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name} ENGINE = Atomic;")

    def load_unpacked_from_records(self, schema_name, table_name, columns, records):
        final = schema_name + "." + table_name
        working = with_random_suffix(final, "working")
        tombstone = with_random_suffix(final, "tombstone")
        self._ensure_schema(schema_name)

        p = InsertProgress(
            make_message=lambda count, last_row: f"Processed {count} records to {working}, last was {last_row}"
        )

        column_names = [c[0] for c in columns]
        column_types = [_data_type_to_clickhouse_type(c[1]) for c in columns]
        cols = [name + " " + type for name, type in zip(column_names, column_types)]

        client = self.client()
        query = f"""
            CREATE TABLE {working} (
                _extracted_at DateTime64 DEFAULT toDateTime64(now(), 3, 'UTC'),
        {", ".join(cols)}
            )
            ENGINE MergeTree()
            ORDER BY (_extracted_at);"""
        client.execute(query)
        p.display(f"Created {query}")

        insert = f"""INSERT INTO {working} ({', '.join(column_names)}) VALUES"""
        p.display(f"Insert query: {insert}")

        def record_for_clickhouse(record):
            row = [record.data[column] for column in column_names]
            p.update(row)
            return row

        client.execute(
            insert, (record_for_clickhouse(row) for row in records), types_check=True
        )

        p.display()

        if client.table_exists(schema_name, table_name):
            client.execute(f"RENAME TABLE {final} to {tombstone};")
            client.execute(f"RENAME TABLE {working} to {final};")
            client.execute(f"DROP TABLE {tombstone};")
        else:
            client.execute(f"RENAME TABLE {working} to {final};")

    def load_raw_from_records(self, schema_name, table_name, records):
        final = schema_name + "." + table_name
        working = with_random_suffix(final, "working")
        tombstone = with_random_suffix(final, "tombstone")
        self._ensure_schema(schema_name)

        client = self.client()

        p = InsertProgress(
            make_message=lambda count, last_row: f"Processed {count} records to {working}, last was {last_row}"
        )

        def record_for_clickhouse(record):
            row = [record.data_str, record.extracted_at]
            p.update(row)
            return row

        client.execute(
            f"""CREATE TABLE IF NOT EXISTS {working} (
                    data String,
                    _extracted_at DateTime64 DEFAULT toDateTime64(now(), 3, 'UTC'))
                ENGINE MergeTree()
                ORDER BY (_extracted_at);"""
        )
        insert = f"""INSERT INTO {working} (data, _extracted_at) VALUES"""
        num_rows = client.execute(
            insert, (record_for_clickhouse(row) for row in records)
        )

        p.display()

        if client.table_exists(schema_name, table_name):
            client.execute(f"RENAME TABLE {final} to {tombstone};")
            client.execute(f"RENAME TABLE {working} to {final};")
            client.execute(f"DROP TABLE {tombstone};")
        else:
            client.execute(f"RENAME TABLE {working} to {final};")
        p.display(f"Renamed {working} to {final}")

        table = Table(store=self, schema_name=schema_name, table_name=table_name)

        return {
            "count": num_rows,
            "rows": table.sample(
                limit=max(23, num_rows),
                order_by="rand()",
                where=f"inserted_at = (select max(inserted_at) FROM {final})",
            ),
        }

    def create_or_replace_model(self, table_name, schema_name, select):
        final = schema_name + "." + table_name
        working = with_random_suffix(final, "working")
        tombstone = with_random_suffix(final, "tombstone")

        client = self.client()

        def make_message(progress):
            num_rows, total_rows = progress
            if total_rows != 0:
                return f"Processed {int(100 * (float(num_rows) / total_rows)) : 02d}% ({num_rows} / {total_rows}) to {working}"
            else:
                return f"Processed {num_rows} to {working}"

        p = GaugeProgress(make_message=make_message)

        self._ensure_schema(schema_name)
        p.display(f"Schema {schema_name} exists.")

        query = client.execute_with_progress(
            f"CREATE TABLE {working} ENGINE = MergeTree() ORDER BY order_by AS {select};"
        )
        for num_rows, total_rows in query:
            p.update([num_rows, total_rows])

        res = query.get_result()
        p.display(f"Table {working} created: {res}")

        if client.table_exists(schema_name, table_name):
            client.execute(f"RENAME TABLE {final} to {tombstone};")
            client.execute(f"RENAME TABLE {working} to {final};")
            client.execute(f"DROP TABLE {tombstone};")
        else:
            client.execute(f"RENAME TABLE {working} to {final};")

    def get_table(self, schema_name, table_name):
        return Table(store=self, schema_name=schema_name, table_name=table_name)

    def execute(self, statement):
        return _execute(self.client(), statement)


def _execute(client, statement):
    res = client.execute_iter(statement, with_column_types=True)
    cols = next(res)

    for data in res:
        row = {}
        for value, col in zip(data, cols):
            row[col[0]] = to_sample_value(value)
        yield row


class Table(BaseTable):
    def _sample(self, limit, order_by, where):
        stmt = f"SELECT * FROM {self.schema_name}.{self.table_name}"
        if where is not None:
            stmt += f" WHERE {where} "
        if order_by is not None:
            stmt += f" ORDER BY {order_by} "
        if limit is not None:
            stmt += f" LIMIT {limit} "
        return _execute(self.store.client(), stmt)
