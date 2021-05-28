import runpy
import traceback
from itertools import chain
from pathlib import Path

import pygit2

from libds.data_node import DataOrchestrator
from libds.model import BaseModel
from libds.source import BaseSource, BrokenSource
from libds.store import BaseStore
from libds.utils import (
    DoesNotExist,
    ThreadLocalList,
    ThreadLocalValue,
    yaml_dump,
    yaml_load,
)

LOCAL_DATA_STACKS = ThreadLocalList()
LOCAL_SOURCES = ThreadLocalList()
LOCAL_STORES = ThreadLocalList()

CURRENT_FILENAME = ThreadLocalValue()
CURRENT_DATA_STACK = ThreadLocalValue()


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
            ds = DataStack(directory=dir, config=yaml_load(file=data_stack_yaml))

        if ds is None:
            raise Exception("No data stack defined.")

        ds.directory = dir
        return ds

    def info(self):
        repo = pygit2.Repository(self.directory)
        head = repo.revparse_single("HEAD")
        return dict(
            config=self.config,
            repo=dict(
                head=dict(
                    message=head.raw_message.decode("utf-8").strip(),
                    author=f'"{head.author.name}" <{head.author.email}>',
                ),
                branch=repo.head.shorthand,
            ),
            sources=[s.info() for s in self.sources],
            store=self.store.info(),
            models=[model.info() for model in self.models],
            data=self.data_orchestrator.info(),
        )

    def load_data_orchestrator(self):
        # NOTE not the cleanest code, DataOrchestrator depends on the
        # data_nodes having been initilized. but the whole data stack
        # loading logic is weird, needs a long think and
        # refactoring. 20210408:mb
        self.data_orchestrator = DataOrchestrator(self)

        for data in self.sources + self.models:
            self.data_orchestrator.collect_nodes(data.data_nodes())

        self.data_orchestrator.post_load_backpatch()

        self.data_orchestrator.load_node_states()

    def sources_dir(self):
        dir = self.directory / "sources"
        dir.mkdir(parents=True, exist_ok=True)
        return dir

    def load_sources(self):
        CURRENT_DATA_STACK.value = self
        self.sources = []
        files = list(self.sources_dir().glob("*.py"))
        for source_py in sorted(files, key=lambda p: str(p).lower()):
            try:
                source_py = source_py.resolve()
                CURRENT_FILENAME.value = source_py
                LOCAL_SOURCES.reset()
                runpy.run_path(source_py, run_name="local")
                self.sources.extend(LOCAL_SOURCES)
            except Exception:
                self.sources.append(
                    BrokenSource(
                        data_stack=self,
                        filename=source_py,
                        error=traceback.format_exc(),
                    )
                )

        for file in self.sources_dir().glob("*.yaml"):
            CURRENT_FILENAME.value = file
            try:
                cls = BaseSource.class_from_yaml(self, file)
                source = cls.load_from_yaml(self, file)

            except:  # noqa: E722
                source = BrokenSource(
                    data_stack=self,
                    filename=file,
                    error=traceback.format_exc(),
                )
            self.sources.append(source)

    def update_file(self, filename, source):
        path = self.directory / filename
        path.open("w").write(source)
        return path

    def set_file_nodes_stale(self, filename):
        dir = filename.parent.name
        basename = filename.stem
        if dir == "models":
            resource = self.get_model(basename)
        elif dir == "sources":
            resource = self.get_source(basename)
        else:
            raise ValueError(f"{filename} is neither a model/ nor a source/")

        for n in resource.data_nodes():
            self.data_orchestrator.set_node_stale(n.id)

    def delete_file(self, filename):
        path = self.directory / filename
        if path.exists():
            path.unlink()
        return path

    def move_file(self, src, dst):
        src = self.directory / src
        if not src.exists():
            raise ValueError("SRC path {src} does not exist")
        if dst.exists():
            raise ValueError("DST path {dst} already exists")
        src.rename(dst)

    def get_source(self, id):
        for s in self.sources:
            if s.id == id:
                return s
        else:
            return None

    def models_dir(self):
        dir = self.directory / "models"
        dir.mkdir(parents=True, exist_ok=True)
        return dir

    def load_models(self):
        CURRENT_DATA_STACK.value = self
        sqls = self.models_dir().glob("**/*.sql")
        pys = self.models_dir().glob("**/*.py")
        models = [BaseModel.from_file(self, filename) for filename in chain(sqls, pys)]
        self.models = list(filter(None, models))
        CURRENT_DATA_STACK.value = None

    def get_model(self, id):
        for model in self.models:
            if model.id == id:
                return model
        else:
            raise DoesNotExist(f"Model: {id}")

    def stores_dir(self):
        dir = self.directory / "stores"
        dir.mkdir(parents=True, exist_ok=True)
        return dir

    def create_default_store(self):
        path = self.stores_dir() / "store.yaml"
        yaml_dump(
            dict(
                type="libds.store.sqlite.SQLite",
                path="./store.sqlite3",
            ),
            path,
        )
        BaseStore.from_file(path)

    def load_store(self):
        LOCAL_STORES.reset()
        CURRENT_DATA_STACK.value = self
        for filename in chain(
            self.stores_dir().glob("**/*.py"), self.stores_dir().glob("**/*.yaml")
        ):
            BaseStore.from_file(filename)
        if len(LOCAL_STORES) > 1:
            raise Exception(f"Multiple Stores defined in {self.directory}")
        if len(LOCAL_STORES) == 0:
            self.create_default_store()
        CURRENT_DATA_STACK.value = None
        self.store = LOCAL_STORES[0]

    def load(self):
        # NOTE models can depend on the store, make sure to load that
        # first. 20210528:mb
        self.load_store()
        self.load_sources()
        self.load_models()
        self.load_data_orchestrator()

        return self
