from libds import DataStack


def test_config_from_yaml(fixtures):
    ds0 = DataStack.from_dir(fixtures.dir("ds0"))
    assert ds0.sources == []


def test_sources_exist(fixtures):
    ds1 = DataStack.from_dir(fixtures.dir("ds1"))
    assert len(ds1.sources) == 1
    table = ds1.sources[0]
    assert table.columns == " a  b  c ".split()
    assert [r.data for r in table.collect_new_records(None)] == [
        {"a": "1", "b": "2", "c": "3"},
        {"a": "4", "b": "5", "c": "6"},
    ]


def test_sources_from_yaml(fixtures):
    ds2 = DataStack.from_dir(fixtures.dir("ds2"))
    assert len(ds2.sources) == 3
    table = ds2.sources[0]
    assert table.columns == " a  b  c ".split()
    assert [r.data for r in table.collect_new_records(None)] == [
        {"a": "1", "b": "2", "c": "3"},
        {"a": "4", "b": "5", "c": "6"},
    ]
