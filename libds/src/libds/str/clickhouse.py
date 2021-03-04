import json

from clickhouse_driver import Client

from libds.str import BaseTable, Store


class ClickHouseClient:
    def __init__(self, **kwargs):
        self.client = Client(**kwargs)

    def execute(self, stmt, *args, **kwargs):
        # print(f"Executing `{stmt}`")
        return self.client.execute(stmt, *args, **kwargs)


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
            host=self.parameters["host"], port=self.parameters["port"]
        )

    def append_records(self, schema_name, table_name, records, recreate):
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

        if recreate:
            client.execute(f"TRUNCATE TABLE IF EXISTS {full_name}_raw;")

        def row_for_clickhouse(row):
            if row.primary_key is None:
                has_primary_key = 0
                primary_key = ""
            else:
                has_primary_key = 1
                primary_key = row.primary_key
            data = json.dumps(row.data)
            if row.valid_at is None:
                valid_at = ""
            else:
                valid_at = row.valid_at.isoformat()
            return [has_primary_key, primary_key, data, valid_at]

        num_rows = client.execute(
            f"""INSERT INTO {full_name}_raw (has_primary_key, primary_key, data, valid_at) VALUES""",
            (row_for_clickhouse(row) for row in records),
        )

        table = Table(
            store=self, schema_name=schema_name, table_name=table_name + "_raw"
        )

        return {
            "count": num_rows,
            "rows": table.sample(
                limit=max(23, num_rows),
                order_by="rand()",
                where=f"inserted_at = (select max(inserted_at) FROM {full_name}_raw)",
            ),
        }

    def create_or_replace_transformation(self, table_name, schema_name, select):
        client = self.client()
        client.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name} ENGINE = Atomic;")
        client.execute(f"DROP TABLE IF EXISTS {schema_name}.{table_name};")
        client.execute(
            f"CREATE TABLE {schema_name}.{table_name} ENGINE = MergeTree() ORDER BY id AS {select};"
        )

    def get_table(self, schema_name, table_name):
        return Table(store=self, schema_name=schema_name, table_name=table_name)


class Table(BaseTable):
    def _sample(self, limit, order_by, where):
        client = self.store.client()
        stmt = f"SELECT * FROM {self.schema_name}.{self.table_name}"
        if where is not None:
            stmt += f" WHERE {where} "
        if order_by is not None:
            stmt += f" ORDER BY {order_by} "
        if limit is not None:
            stmt += f" LIMIT {limit} "
        iter, cols = client.execute(stmt, with_column_types=True)

        rows = []
        for data in iter:
            row = {}
            for value, col in zip(data, cols):
                row[col[0]] = self.to_sample_value(value)
            rows.append(row)

        return rows
