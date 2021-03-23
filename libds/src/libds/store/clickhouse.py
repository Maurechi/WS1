import sys

import arrow
import clickhouse_driver.errors
from clickhouse_driver import Client

from libds.store import BaseTable, Store, to_sample_value
from libds.utils import Progress


class ClickHouseClient:
    def __init__(self, **kwargs):
        self.client = Client(**kwargs)

    def execute(self, stmt, *args, **kwargs):
        # print(f"Executing `{stmt}`")
        try:
            return self.client.execute(stmt, *args, **kwargs)
        except clickhouse_driver.errors.ServerException as se:
            print(f"Failed on query {stmt}")
            raise se


class ClickHouse(Store):
    def __init__(self, port=None, host=None, **store_kwargs):
        self.parameters = dict(port=9000, host="localhost")
        if port is not None:
            self.parameters["port"] = port
        if host is not None:
            self.parameters["host"] = host
        super().__init__()

    def info(self):
        return self._info(parameters=self.parameters)

    def client(self):
        return ClickHouseClient(
            host=self.parameters["host"],
            port=self.parameters["port"],
            database="public",
        )

    def _ensure_raw_table(self, schema_name, table_name):
        client = self.client()
        client.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name} ENGINE = Atomic;")
        full_name = schema_name + "." + table_name
        client.execute(
            f"""CREATE TABLE IF NOT EXISTS {full_name}_raw (
                    has_primary_key UInt8,
                    primary_key String,
                    data String,
                    valid_at String,
                    inserted_at DateTime64 DEFAULT toDateTime64(now(), 3, 'UTC'))
                ENGINE MergeTree()
                ORDER BY (primary_key, inserted_at);"""
        )
        client.execute(
            f"""CREATE TABLE IF NOT EXISTS {full_name}_del (
                    deleted_at DateTime64 DEFAULT toDateTime64(now(), 3, 'UTC'),
                    primary_key String)
                ENGINE MergeTree()
                ORDER BY (primary_key, deleted_at);"""
        )
        return client, full_name

    def most_recent_raw_timestamp(self, schema_name, table_name):
        client, full_name = self._ensure_raw_table(schema_name, table_name)
        rows = list(client.execute(f"SELECT max(valid_at) FROM {full_name}_raw"))
        if len(rows) == 1 and len(rows[0]) == 1:
            val = rows[0][0]
            if val == "":
                return None
            else:
                return arrow.get(rows[0][0])
        else:
            return None

    def truncate_raw_table(self, schema_name, table_name):
        client, full_name = self._ensure_raw_table(schema_name, table_name)
        client.execute(f"TRUNCATE TABLE {full_name}_raw")
        client.execute(f"TRUNCATE TABLE {full_name}_del")

    def append_raw(self, schema_name, table_name, records):
        client, full_name = self._ensure_raw_table(schema_name, table_name)
        raw_name = full_name + "_raw"

        progress = Progress(
            lambda c, rec: print(
                f"Processed {c} records to {full_name}, last was {rec}",
                flush=True,
                file=sys.stderr,
            )
        )

        def record_for_clickhouse(record):

            if record.primary_key is None:
                has_primary_key = 0
                primary_key = ""
            else:
                has_primary_key = 1
                primary_key = record.primary_key
            if record.valid_at is None:
                valid_at = ""
            else:
                valid_at = record.valid_at.isoformat()
            values = [has_primary_key, primary_key, record.data_str, valid_at]
            progress.tick(values)
            return values

        insert = f"""INSERT INTO {raw_name} (has_primary_key, primary_key, data, valid_at) VALUES"""
        num_rows = client.execute(
            insert, (record_for_clickhouse(row) for row in records)
        )

        table = Table(
            store=self, schema_name=schema_name, table_name=table_name + "_raw"
        )

        return {
            "count": num_rows,
            "rows": table.sample(
                limit=max(23, num_rows),
                order_by="rand()",
                where=f"inserted_at = (select max(inserted_at) FROM {raw_name})",
            ),
        }

    def create_or_replace_model(self, table_name, schema_name, select):
        client = self.client()
        client.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name} ENGINE = Atomic;")
        client.execute(f"DROP TABLE IF EXISTS {schema_name}.{table_name};")
        client.execute(
            f"CREATE TABLE {schema_name}.{table_name} ENGINE = MergeTree() ORDER BY order_by AS {select};"
        )

    def get_table(self, schema_name, table_name):
        return Table(store=self, schema_name=schema_name, table_name=table_name)

    def execute(self, statement):
        return _execute(self.client(), statement)


def _execute(client, statement):
    iter, cols = client.execute(statement, with_column_types=True)

    rows = []
    for data in iter:
        row = {}
        for value, col in zip(data, cols):
            row[col[0]] = to_sample_value(value)
        rows.append(row)

    return rows


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
