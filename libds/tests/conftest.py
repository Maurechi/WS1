import os
import tempfile as tmpfile
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from libds import DataStack


def _ds(fixture_dir):
    return DataStack(directory=(Path(__file__).parent / "fixtures" / fixture_dir).resolve())


class Fixtures:
    def __init__(self, directory):
        self.directory = directory

    def dir(self, dir):
        return self.directory / dir


@pytest.fixture()
def fixtures():
    return Fixtures(directory=(Path(__file__).parent / "fixtures").resolve())


@pytest.fixture()
def yaml():
    return YAML(typ="safe")


@pytest.fixture()
def tempfile():
    fd, path = tmpfile.mkstemp(suffix=".sqlite3", prefix="libds_test_")
    os.close(fd)
    yield path
    os.unlink(path)
