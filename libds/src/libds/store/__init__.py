import datetime
from decimal import Decimal


class Store:
    def __init__(self, data_stack=None, id=None, filename=None):
        from libds.data_stack import (
            CURRENT_DATA_STACK,
            CURRENT_FILENAME,
            LOCAL_STORES,
        )

        self.data_stack = data_stack or CURRENT_DATA_STACK.value
        self.filename = None
        self._id = id

        if filename is not None:
            self.filename = filename
        elif CURRENT_FILENAME.value is not None:
            self.filename = CURRENT_FILENAME.value

        LOCAL_STORES.append(self)

    @property
    def type(self):
        return self.__class__.__module__ + "." + self.__class__.__name__

    @property
    def id(self):
        if self._id is not None:
            return self._id
        elif self.filename is not None:
            return self.filename.stem
        else:
            return None

    def _info(self, **data):
        defaults = dict(
            type=self.type,
            id=self.id,
        )
        return {**defaults, **data}

    def info(self):
        return self._info()

    def execute(self, store):
        raise NotImplementedError()


def to_sample_value(value):
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    elif isinstance(value, (bool, int, str, type(None), float)):
        return value
    else:
        raise ValueError(f"Don't know how to make a sample datum from {value}.")


class BaseTable:
    def __init__(self, store, schema_name, table_name):
        self.store = store
        self.schema_name = schema_name
        self.table_name = table_name

    def sample(self, limit=None, order_by=None, where=None):
        if limit is None:
            limit = 23
        return self._sample(limit, order_by, where)
