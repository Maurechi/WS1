import pytest
from diaas_testing import Expect

import diaas.app


@pytest.fixture(scope="session")
def app():
    return diaas.app.create_app()


@pytest.fixture()
def client(app):
    app.config["TESTING"] = True
    return app.test_client()


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Expect):
        return left.msg
