import pytest

import diaas.app


@pytest.fixture(scope="session")
def app():
    return diaas.app.create_app()


@pytest.fixture()
def client(app):
    app.config["TESTING"] = True
    return app.test_client()
