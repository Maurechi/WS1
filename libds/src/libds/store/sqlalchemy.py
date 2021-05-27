import datetime
from decimal import Decimal

import sqlalchemy as sa

from libds.store import BaseStore, BaseTable


class SQLAlchemyStore(BaseStore):
    def __init__(self, url=None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.metadata = sa.MetaData()
        if self.url is not None:
            self.engine = sa.create_engine(self.url, echo=False)


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
