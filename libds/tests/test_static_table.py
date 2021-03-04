from libds.src.static import StaticTable


def test_1():
    s = StaticTable.from_data(
        """
a
1
2
3
"""
    )
    assert s.columns == ["a"]
    assert s.rows == [["1"], ["2"], ["3"]]


def test_2():
    s = StaticTable.from_data(
        """
a b "c and d"
1
2
3
"""
    )
    assert s.columns == ["a", "b", "c and d"]


def test_3():
    s = StaticTable.from_data(
        """
a
1, '4 \\and'\\ 5
"""
    )
    assert s.columns == ["a"]
    assert s.rows == [["1,", "4 \\and 5"]]


def test_4(fixtures, yaml):
    s = StaticTable.from_config(yaml.load(fixtures.dir("ds2") / "sources" / "static_table.yaml"))
    assert s.columns == "Date Value".split()
    assert s.rows == [[" row 1", "a b"], ["row \"' 2", "something-elseßáà,entirely"]]
    assert s.name == "A Static Table"


def test_5():
    s = StaticTable.from_data(
        """
a
1
"""
    )
    assert "name" not in s.info()
