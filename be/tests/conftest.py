import pytest
from diaas_testing import Expect

from diaas.app import create_app


@pytest.fixture(scope="session")
def app():
    return create_app(testing=True)


@pytest.fixture()
def client(app):
    return app.test_client()


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Expect):
        return left.msg
