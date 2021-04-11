import sqlalchemy as sa

from libds.source import SQLAlchemyStore


class SQLite(SQLAlchemyStore):
    def __init__(self, path):
        if path == ":memory:":
            url = "sqlite+pysqlite://"
        else:
            url = f"sqlite+pysqlite:///{path}"
        self.path = path
        super().__init__(url=url)

    def info(self):
        return self._info(path=self.path)

    def make_table_name(self, schema_name, table_name):
        return f"{schema_name}_{table_name}"

    def truncate_raw_table(self, schema_name, table_name):
        table_name = self.make_table_name(schema_name, table_name)
        with self.engine.connect() as conn:
            conn.execute(sa.text(f"""DROP TABLE IF EXISTS {table_name}_raw"""))

    def update_raw_with_records(self, schema_name, table_name, records):
        table_name = self.make_table_name(schema_name, table_name)

        with self.engine.connect() as conn:
            conn.execute(
                sa.text(
                    f"""
                CREATE TABLE IF NOT EXISTS {table_name}_raw (
                  primary_key text,
                  data text not null,
                  valid_at text,
                  ins_at text default current_timestamp,
                );"""
                )
            )

        return self._insert_rows(table_name, records)

    def create_or_replace_model(self, table, schema, select):
        with self.engine.connect() as conn:
            view_name = self.make_table_name(schema, table)
            conn.execute(sa.text(f"DROP VIEW IF EXISTS {view_name};"))
            conn.execute(sa.text(f"CREATE VIEW {view_name} AS {select};"))
