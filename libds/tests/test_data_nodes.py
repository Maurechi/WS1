from datetime import timedelta
from libds.utils import parse_timedelta


def test_parse_timedelta():
    assert parse_timedelta("1s") == timedelta(seconds=1)
    assert parse_timedelta("10s") == timedelta(seconds=10)
    assert parse_timedelta("100s") == timedelta(seconds=100)
    assert parse_timedelta("7h") == timedelta(seconds=7 * 3600)
    assert parse_timedelta("70m") == timedelta(seconds=60 * 70)
    assert parse_timedelta("86400s") == timedelta(days=1)
    assert parse_timedelta("86401s") == timedelta(seconds=86401)
    assert parse_timedelta("24h") == timedelta(days=1)
