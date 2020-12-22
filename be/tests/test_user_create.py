from uuid import uuid4

from diaas.model import User


def test_user_create(app):
    with app.app_context():
        email = f"{uuid4()}@example.com"
        u = User.ensure_user(email=email)
        from pprint import pprint

        pprint(u.data_stacks)
        u2 = u = User.query.filter(User.email == email).one_or_none()
        assert u2
        assert len(u2.data_stacks) == 1
        assert u2.data_stacks[0] is None
