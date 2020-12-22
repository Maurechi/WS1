from diaas.model import User
from uuid import uuid4


def test_user_create(app):
    with app.app_context():
        u = User.ensure_user(email=f"{uuid4()}@example.com")
        from pprint import pprint
        pprint(u.data_stacks)
        assert len(u.data_stacks) > 0
