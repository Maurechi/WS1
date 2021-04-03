import datetime
import runpy
from decimal import Decimal

from libds.utils import ThreadLocalList, ThreadLocalValue

CURRENT_DATA_STACK = ThreadLocalValue()
LOCAL_STORES = ThreadLocalList()
CURRENT_FILENAME = ThreadLocalValue()


def load_store(data_stack):
    LOCAL_STORES.reset()
    CURRENT_DATA_STACK.value = data_stack
    for store_py in (data_stack.directory / "stores").glob("**/*.py"):
        store_py = store_py.resolve()
        CURRENT_FILENAME.value = store_py
        runpy.run_path(store_py)
    if len(LOCAL_STORES) == 0:
        # raise Exception(f"No stores defined in {data_stack.directory}")
        return None
    if len(LOCAL_STORES) > 1:
        raise Exception(f"Multiple Stores defined in {data_stack.directory}")
    CURRENT_FILENAME.value = None
    CURRENT_DATA_STACK.value = None
    return LOCAL_STORES[0]


class Store:
    def __init__(self, data_stack=None, id=None, filename=None):
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
