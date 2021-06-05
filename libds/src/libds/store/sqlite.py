import json
from pathlib import Path
from pprint import pprint  # noqa: F401

import sqlalchemy as sa

from libds.store import (
    BaseTable,
    random_suffix_regexp,
    to_sample_value,
    with_random_suffix,
)
from libds.store.sqlalchemy import SQLAlchemyStore
from libds.utils import InsertProgress


class SQLite(SQLAlchemyStore):
    def __init__(self, path):
        if path == ":memory:":
            url = "sqlite+pysqlite://"
        else:
            from libds.data_stack import CURRENT_FILENAME

            dir = CURRENT_FILENAME.value.parent
            joined = dir.joinpath(Path(path))
            resolved = joined.resolve()
            url = f"sqlite+pysqlite:///{resolved}"
        self.parameters = dict(path=path, url=url)
        super().__init__(url=url)

    @classmethod
    def from_yaml(cls, yaml):
        return cls(path=yaml["path"])

    def info(self):
        return self._info(parameters=self.parameters)

    def table_exists(self, conn, schema_name, table_name):
        res = conn.execute(
            "select count(*) as count from sqlite_master where name = :name",
            dict(name=table_name),
        )
        return res.one()["count"]

    def drop_tables_by_tag(self, schema_name, table_name, tag):
        with self.engine.connect() as conn:
            re = random_suffix_regexp(table_name, tag)
            res = conn.execute("select name from sqlite_schema where type = 'table'")
            table_names = [row["name"] for row in res.all() if re.match(row["name"])]
            for table in table_names:
                conn.execute(f'drop table "{table}";')

        return table_names

    def load_raw_from_records(self, schema_name, table_name, records):
        final_name = table_name
        working_name = with_random_suffix(final_name, "working")
        tombstone_name = with_random_suffix(final_name, "tombstone")

        sa.Table(
            working_name,
            self.metadata,
            sa.Column("extracted_at", sa.DateTime),
            sa.Column("data", sa.JSON),
        )
        self.metadata.create_all(self.engine)

        def make_message(num_rows):
            return f"Processed {num_rows} to {working_name}"

        p = InsertProgress(
            make_message=lambda count, last_row: f"Processed {count} records to {working_name}, last was {last_row}"
        )

        def record_for_sqlite(record):
            row = [record.data_str, record.extracted_at]
            p.update(row)
            return row

        with self.engine.connect() as conn:
            for rec in records:
                conn.execute(
                    f"insert into {working_name} (data, extracted_at) values (:data, :extracted_at)",
                    dict(data=json.dumps(rec.data), extracted_at=rec.extracted_at),
                )

            p.display()

            if self.table_exists(conn, schema_name, table_name):
                conn.execute(f"ALTER TABLE {final_name} RENAME TO {tombstone_name};")
                conn.execute(f"ALTER TABLE {working_name} RENAME TO {final_name};")
                conn.execute(f"DROP TABLE {tombstone_name};")
            else:
                conn.execute(f"ALTER TABLE {working_name} RENAME TO {final_name};")

            p.display(f"Renamed {working_name} to {final_name}")

            self._cleanup_tables(p, schema_name, final_name)

        table = Table(store=self, schema_name=schema_name, table_name=table_name)

        return {
            "count": None,
            "rows": table.sample(
                limit=23,
                order_by="rand()",
                where=f"inserted_at = (select max(inserted_at) FROM {final_name})",
            ),
        }

    def create_or_replace_model(self, schema_name, table_name, select):
        final_name = table_name
        working_name = with_random_suffix(final_name, "working")
        tombstone_name = with_random_suffix(final_name, "tombstone")

        p = InsertProgress(
            make_message=lambda count: f"Processed {count} records to {working_name}"
        )

        def record_for_sqlite(record):
            row = [record.data_str, record.extracted_at]
            p.update(row)
            return row

        with self.engine.connect() as conn:
            conn.execute(f"create table {working_name} as {select}")

            p.display(f"Created {working_name}")

            if self.table_exists(conn, schema_name, table_name):
                conn.execute(f"ALTER TABLE {final_name} RENAME TO {tombstone_name};")
                conn.execute(f"ALTER TABLE {working_name} RENAME TO {final_name};")
                conn.execute(f"DROP TABLE {tombstone_name};")
            else:
                conn.execute(f"ALTER TABLE {working_name} RENAME TO {final_name};")

            p.display(f"Renamed {working_name} to {final_name}")

            self._cleanup_tables(p, schema_name, final_name)

    def execute_sql(self, stmt):
        return _execute(self, stmt)

    def model_id_to_table_name(self, model_id):
        parts = model_id.split(".")
        if len(parts) == 1:
            return model_id
        else:
            return parts[1]


def _execute(store, statement):
    with store.engine.connect() as conn:
        res = conn.execute(statement, with_column_types=True)
        for row in res.all():
            yield {f: to_sample_value(row[f]) for f in row._fields}


class Table(BaseTable):
    def _sample(self, limit, order_by, where):
        stmt = f"SELECT * FROM {self.table_name}"
        if where is not None:
            stmt += f" WHERE {where} "
        if order_by is not None:
            stmt += f" ORDER BY {order_by} "
        if limit is not None:
            stmt += f" LIMIT {limit} "
        return _execute(self.store, stmt)
