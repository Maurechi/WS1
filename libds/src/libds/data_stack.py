import runpy
from pathlib import Path

import pygit2
from ruamel.yaml import YAML

from libds.model import load_models
from libds.source import load_sources
from libds.store import load_store
from libds.utils import ThreadLocalList

LOCAL_DATA_STACKS = ThreadLocalList()


class DataStack:
    def __init__(self, directory=None, config={}):
        self.directory = directory
        self.config = config
        LOCAL_DATA_STACKS.append(self)

    @classmethod
    def from_dir(self, path):
        dir = Path(path)
        if not dir.exists():
            raise ValueError(
                f"Can't load a DataStack from the inexistent directory {path}"
            )
        ds = None

        data_stack_py = dir / "data_stack.py"
        if data_stack_py.exists():
            LOCAL_DATA_STACKS.reset()
            runpy.run_path(data_stack_py)
            if len(LOCAL_DATA_STACKS) == 0:
                raise Exception(f"No DataStack defined in {data_stack_py}")
            if len(LOCAL_DATA_STACKS) > 1:
                raise Exception(f"Multiple DataStacks defined in {data_stack_py}")
            ds = LOCAL_DATA_STACKS[0]

        data_stack_yaml = dir / "data_stack.yaml"
        if data_stack_yaml.exists():
            yaml = YAML(typ="safe")
            ds = DataStack(config=yaml.load(data_stack_yaml))

        if ds is None:
            raise Exception("No data stack defined.")

        ds.directory = dir
        return ds

    def info(self):
        repo = pygit2.Repository(self.directory)
        head = repo.revparse_single("HEAD")
        remotes = repo.remotes
        if len(remotes) == 1:
            remote = remotes[0]
        else:
            remote = remotes["origin"]
        return dict(
            config=self.config,
            repo=dict(
                head=dict(
                    message=head.raw_message.decode("utf-8").strip(),
                    author=f'"{head.author.name}" <{head.author.email}>',
                ),
                branch=repo.head.shorthand,
                origin=dict(
                    name=remote.name,
                    url=remote.url,
                ),
            ),
            sources=[s.info() for s in self.sources],
            stores=[store.info() for store in self.stores],
            models=[model.info() for model in self.models],
        )

    @property
    def sources(self):
        return load_sources(self)

    def get_source(self, id):
        for s in self.sources:
            if s.id == id:
                return s
        else:
            return None

    @property
    def stores(self):
        store = load_store(self)
        if store is None:
            return []
        else:
            return [store]

    @property
    def store(self):
        stores = self.stores
        if len(stores) > 0:
            return stores[0]
        else:
            return None

    @property
    def models(self):
        return load_models(self)

    def get_model(self, id):
        for model in self.models:
            if model.id == id:
                return model
        else:
            return None

    @property
    def models_dir(self):
        return self.directory / "models"
