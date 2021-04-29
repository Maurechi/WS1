from libds.model import data_type as dt
from libds.store.clickhouse import _data_type_to_clickhouse_type


def test_clickhouse_data_types():
    assert _data_type_to_clickhouse_type(dt.Integer(32)) == "Int32"
    assert _data_type_to_clickhouse_type(dt.Integer(10)) == "Int16"
    assert _data_type_to_clickhouse_type(dt.Integer(1)) == "Int8"
    assert _data_type_to_clickhouse_type(dt.Integer(8)) == "Int8"
