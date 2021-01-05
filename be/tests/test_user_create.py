import json
import subprocess
from uuid import uuid4

from diaas.config import CONFIG
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
        ds = u2.data_stacks[0]
        assert ds.path.exists()
        branch = subprocess.check_output(["git", "-C", str(ds.path), "branch", "--show-current"], text=True)
        assert branch.strip() == "prd"

        remote_name = subprocess.check_output(["git", "-C", str(ds.path), "remote", "show"], text=True)
        assert remote_name.strip() == "origin"

        remote_url = subprocess.check_output(["git", "-C", str(ds.path), "remote", "get-url", "origin"], text=True)
        assert remote_url.strip().startswith(str(CONFIG.DS_STORE))

        subprocess.check_call([str(ds.path / "build")], text=True)
        info_text = subprocess.check_output([str(ds.path / "run")] + "ds -f json info".split(), text=True)
        info = json.loads(info_text)
        assert "sources" in info
        assert info["sources"] == []
