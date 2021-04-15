from copy import copy
from urllib.parse import urlencode

import sqlalchemy as sa

from libds.store.sqlalchemy import SQLAlchemyStore
from libds.utils import hash_password


class PostgreSQL(SQLAlchemyStore):
    def __init__(self, **parameters):
        self.parameters = parameters
        url = "postgresql+psycopg2:///?" + urlencode(parameters)
        super().__init__(url=url)

    def info(self):
        parameters = copy(self.parameters)
        if "password" in parameters:
            parameters["password"] = hash_password(parameters["password"])
        return self._info(parameters=parameters)

    def make_table_name(self, schema_name, table_name):
        return f"{schema_name}.{table_name}"

    def update_raw_with_records(self, schema_name, table_name, records):
        table_name = self.make_table_name(schema_name, table_name)
        with self.engine.connect() as conn:
            conn.execute(sa.text(f"""CREATE SCHEMA IF NOT EXISTS {schema_name}"""))
            conn.execute(
                sa.text(
                    f"""CREATE TABLE IF NOT EXISTS {table_name} (
                          primary_key text,
                          data jsonb not null,
                          valid_at timestamptz,
                        );"""
                )
            )

        return self._insert_rows(table_name, records)

    def create_or_replace_model(self, table, schema, select):
        with self.engine.connect() as conn:
            view_name = self.make_table_name(schema, table)
            # NOTE we need to drop the view here as postgresql does
            # not support using `create or repalce view` in the case
            # where the columns and types of the query have changed,
            # and we do not yet have any way to detect if that is the
            # case. 20210116:mb
            conn.execute(sa.text(f"DROP VIEW IF EXISTS {view_name} CASCADE;"))
            conn.execute(sa.text(f"CREATE VIEW {view_name} AS {select};"))
