import datetime
import json
from decimal import Decimal

import sqlalchemy as sa

from libds.store import BaseTable, Store


class SQLAlchemyStore(Store):
    def __init__(self, url=None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.metadata = sa.MetaData()
        if self.url is not None:
            self.engine = sa.create_engine(self.url, echo=False)

    def _insert_rows(self, table_name, rows):
        count = 0
        conn = self.engine.connect()
        inserted = []
        with conn.begin():
            for r in rows:
                count += 1
                inserted.append(r.data)
                conn.execute(
                    sa.text(f"INSERT INTO {table_name} (data) VALUES (:data)"),
                    dict(data=json.dumps(r.data)),
                )
        return {"count": count, "rows": inserted}

    def get_table(self, schema_name, table_name):
        return Table(store=self, schema_name=schema_name, table_name=table_name)

    def execute_sql(self, stmt):
        with self.engine.connect() as conn:
            conn.execute(sa.text(stmt))


class Table(BaseTable):
    def sample(self, limit=None, order_by=None):
        if limit is None:
            limit = 23
        if order_by is not None:
            order_by = f"ORDER BY {order_by}"
        else:
            order_by = ""
        with self.store.engine.connect() as conn:
            table_name = self.store.make_table_name(self.schema_name, self.table_name)
            res = conn.execute(
                sa.text(f"""SELECT * FROM {table_name} {order_by} LIMIT :limit"""),
                limit=limit,
            )

            rows = []
            columns = sorted(res.keys())
            for row in res:
                plain_row = {}
                for col in columns:
                    value = row[col]
                    if isinstance(value, Decimal):
                        value = float(value)
                    elif isinstance(value, (datetime.datetime, datetime.date)):
                        value = value.isoformat()
                    elif not isinstance(value, (bool, int, str, type(None))):
                        raise ValueError(
                            "Don't know how to amke db value {value} plain."
                        )
                    plain_row[col] = value
                rows.append(plain_row)
            return rows
