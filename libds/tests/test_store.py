import json
import os
import sqlite3
import subprocess

from libds import DataStack


def test_store_is_created(fixtures):
    ds3 = DataStack.from_dir(fixtures.dir("ds3"))
    assert ds3.store is not None
    assert len(ds3.sources) == 1


def test_source_can_load(fixtures, tempfile):
    os.environ["STORE_PATH"] = tempfile
    ds3 = DataStack.from_dir(fixtures.dir("ds3"))
    store = ds3.store
    assert store is not None
    assert len(ds3.sources) == 1
    source = ds3.sources[0]
    assert source is not None

    source.load()

    conn = store.engine.connect()
    res = conn.execute(
        "select count(*) from sqlite_master where name = 'source_static_table' and type = 'table'"
    ).fetchall()
    assert list(res) == [(1,)]

    res = conn.execute("select insid, data from source_static_table order by insid asc").fetchall()
    assert list(res) == [
        (1, '{"date": "2001-01-01", "value": "ABC", "notes": "some stuff goes here"}'),
        (2, '{"date": "2002-02-02", "value": "DEF", "notes": ""}'),
    ]
    os.environ.pop("STORE_PATH")


def test_source_can_load_from_cli(fixtures, tempfile):
    env = os.environ.copy()
    env["STORE_PATH"] = tempfile
    out_json = subprocess.check_output(
        ["ds", "--directory", str(fixtures.dir("ds3")), "--format", "json", "source-load", "static_table"],
        text=True,
        env=env,
    )
    print(out_json)
    out = json.loads(out_json.strip())
    data = out["data"]
    assert data.get("count") == 2
    conn = sqlite3.connect(tempfile)
    res = conn.execute(
        "select count(*) from sqlite_master where name = 'source_static_table' and type = 'table'"
    ).fetchall()
    assert list(res) == [(1,)]

    res = conn.execute("select insid, data from source_static_table order by insid asc").fetchall()
    assert list(res) == [
        (1, '{"date": "2001-01-01", "value": "ABC", "notes": "some stuff goes here"}'),
        (2, '{"date": "2002-02-02", "value": "DEF", "notes": ""}'),
    ]


def test_source_to_postgresql(fixtures, tempfile):
    ds4 = DataStack.from_dir(fixtures.dir("ds4"))
    source = ds4.sources[0]
    source.load(reload=False)

    conn = ds4.store.engine.connect()
    res = conn.execute(
        "select count(*) from information_schema.tables where table_schema = 'source' and table_name = 'static_table'"
    ).fetchall()
    assert list(res) == [(1,)]

    res = conn.execute("select insid, data from source.static_table order by insid asc").fetchall()
    assert list(res) == [
        (1, {"date": "2001-01-01", "value": "ABC", "notes": "some stuff goes here"}),
        (2, {"date": "2002-02-02", "value": "DEF", "notes": ""}),
    ]
