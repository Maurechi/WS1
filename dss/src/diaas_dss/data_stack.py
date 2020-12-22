import datetime
from pathlib import Path

import pygit2
from jinja2 import Environment, PackageLoader

from diaas_dss.utils import rm_tree


class DataStack:
    def __init__(self, dir=None):
        if dir is None:
            self.dir = Path.cwd()
        else:
            self.dir = Path(dir).resolve()

    def exists(self):
        return self.dir.exists()

    def initialize(self, force=False):
        if self.dir.exists():
            if force:
                rm_tree(self.dir)
            else:
                raise ValueError(f"A DataStack already exsts at {self.dir}")
        self.dir.mkdir(parents=True)
        repo = pygit2.init_repository(self.dir)

        author = pygit2.Signature("Data Stack Service", "dss@diaas.io")
        committer = pygit2.Signature("Data Stack Service", "dss@diaas.io")
        tree = repo.index.write_tree()
        genesis = repo.create_commit(
            "refs/heads/prd", author, committer, "Genesis", tree, []
        )
        repo.checkout("refs/heads/prd")

        env = Environment(loader=PackageLoader("diaas_dss", "templates"))

        vars = dict(now=datetime.datetime.utcnow().isoformat() + "Z")

        for template in ["data_stack.py", "data_stack.yaml"]:
            rendered = env.get_template(template).render(vars)
            target_path = self.dir / template
            with target_path.open("w") as file:
                print(rendered, file=file)

        repo.index.add_all()

        tree = repo.index.write_tree()
        repo.create_commit(
            "refs/heads/prd",
            author,
            committer,
            "Include data_stack files.",
            tree,
            [genesis],
        )
        repo.checkout("refs/heads/prd")

        return self

    def delete(self):
        self.dir.unlink()
        return self

    def extractors(self):
        return []

    def transformations(self):
        return []

    def modules(self):
        return []
