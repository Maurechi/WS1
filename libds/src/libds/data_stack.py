import runpy
from itertools import chain
from pathlib import Path

import pygit2
from ruamel.yaml import YAML

from libds.data_node import DataOrchestrator
from libds.model import BaseModel
from libds.source import BaseSource
from libds.utils import DoesNotExist, ThreadLocalList, ThreadLocalValue

LOCAL_DATA_STACKS = ThreadLocalList()
LOCAL_SOURCES = ThreadLocalList()
LOCAL_STORES = ThreadLocalList()

CURRENT_FILENAME = ThreadLocalValue()
CURRENT_DATA_STACK = ThreadLocalValue()


class DataStack:
    def __init__(self, directory=None, config={}):
        self.directory = directory
        self.config = config
        self.models_dir = self.directory / "models"

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
            ds = DataStack(directory=dir, config=yaml.load(data_stack_yaml))

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
            store=self.store.info(),
            models=[model.info() for model in self.models],
            data_nodes=[node.info() for node in self.data_nodes.values()],
        )

    def register_data_node(self, node):
        return self.register_data_nodes([node])

    def register_data_nodes(self, nodes):
        for node in nodes:
            if node.id in self.data_nodes:
                raise ValueError(
                    f"Attempting to add {node} with id {node.id} but {self.data_nodes[node.id]} already has that key."
                )
            self.data_nodes[node.id] = node

    def load_data_nodes(self):
        self.data_nodes = {}
        for data in self.sources + self.models:
            data.register_data_nodes(data_stack=self)
        # NOTE not the cleanest code, DataOrchestrator depends on the
        # data_nodes having been initilized. but the whole data stack
        # loading logic is weird, needs a long think and
        # refactoring. 20210408:mb
        self.data_orchestrator = DataOrchestrator(self)
        self.data_orchestrator.load()

    def load_sources(self):
        CURRENT_DATA_STACK.value = self
        self.sources = []
        sources_dir = self.directory / "sources"
        files = list(sources_dir.glob("*.py"))
        for source_py in sorted(files, key=lambda p: str(p).lower()):
            source_py = source_py.resolve()
            CURRENT_FILENAME.value = source_py
            LOCAL_SOURCES.reset()
            runpy.run_path(source_py, run_name=f"sources/{source_py.stem}")
            self.sources.extend(LOCAL_SOURCES)

        for file in sources_dir.glob("*.yaml"):
            self.sources.append(BaseSource.load_from_config_file(self, file))

        CURRENT_DATA_STACK.value = None
        CURRENT_FILENAME.value = None
        LOCAL_SOURCES.reset()

    def load_models(self):
        CURRENT_DATA_STACK.value = self
        sqls = self.models_dir.glob("**/*.sql")
        pys = self.models_dir.glob("**/*.py")
        models = [BaseModel.from_file(self, filename) for filename in chain(sqls, pys)]
        self.models = list(filter(None, models))
        CURRENT_DATA_STACK.value = None

    def load_store(self):
        LOCAL_STORES.reset()
        CURRENT_DATA_STACK.value = self
        for store_py in (self.directory / "stores").glob("**/*.py"):
            store_py = store_py.resolve()
            CURRENT_FILENAME.value = store_py
            runpy.run_path(store_py)
        if len(LOCAL_STORES) == 0:
            # raise Exception(f"No stores defined in {self.directory}")
            return None
        if len(LOCAL_STORES) > 1:
            raise Exception(f"Multiple Stores defined in {self.directory}")
        CURRENT_FILENAME.value = None
        CURRENT_DATA_STACK.value = None
        self.store = LOCAL_STORES[0]

    def load(self):
        self.load_sources()
        self.load_models()
        self.load_store()
        self.load_data_nodes()

        return self

    def get_source(self, id):
        for s in self.sources:
            if s.id == id:
                return s
        else:
            return None

    def get_model(self, id):
        # print(f"Looking for model {id} in {list(self.models)}")
        for model in self.models:
            if model.id == id:
                return model
        else:
            raise DoesNotExist(f"Model: {id}")
