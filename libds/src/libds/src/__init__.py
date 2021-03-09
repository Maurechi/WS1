import re
import runpy

from ruamel.yaml import YAML

from libds.utils import ThreadLocalList, ThreadLocalValue


class Row:
    def __init__(self, primary_key, data, valid_at):
        self.primary_key = primary_key
        self.data = data
        self.valid_at = valid_at


CURRENT_DATA_STACK = ThreadLocalValue()
LOCAL_SOURCES = ThreadLocalList()
CURRENT_FILENAME = ThreadLocalValue()


def load_sources(data_stack):
    CURRENT_DATA_STACK.value = data_stack
    sources = []
    sources_dir = data_stack.directory / "sources"
    files = list(sources_dir.glob("*.py"))
    for source_py in sorted(files, key=lambda p: str(p).lower()):
        source_py = source_py.resolve()
        CURRENT_FILENAME.value = source_py
        LOCAL_SOURCES.reset()
        runpy.run_path(source_py, run_name=f"sources/{source_py.stem}")
        sources.extend(LOCAL_SOURCES)

    for file in sources_dir.glob("*.yaml"):
        sources.append(BaseSource.load_from_config_file(data_stack, file))

    CURRENT_DATA_STACK.value = None
    CURRENT_FILENAME.value = None
    LOCAL_SOURCES.reset()
    return sources


class BaseSource:
    def __init__(
        self,
        id=None,
        name=None,
        data_stack=None,
        defined_in="code",
        table_name=None,
    ):
        self._id = id
        self.name = name
        self._table_name = table_name
        self._filename = CURRENT_FILENAME.value
        if data_stack is None:
            data_stack = CURRENT_DATA_STACK.value
        self.data_stack = data_stack
        self.defined_in = defined_in
        LOCAL_SOURCES.append(self)

    @classmethod
    def from_config(cls, config):
        return cls(**config)

    @property
    def type(self):
        return self.__class__.__module__ + "." + self.__class__.__name__

    def row(self, data, modified_at=None, id=None):
        return Row(modified_at=modified_at, id=id, data=data)

    @property
    def id(self):
        if self._id is None:
            if self.filename is None:
                return None
            else:
                return self.filename.stem
        else:
            return self._id

    @property
    def filename(self):
        if self.data_stack is None:
            return self._filename
        else:
            return self._filename.relative_to(self.data_stack.directory)

    @filename.setter
    def filename(self, value):
        self._filename = value
        return value

    def _info(self, **data):
        default = {}
        if self.name is not None:
            default["name"] = self.name
        default["type"] = self.type
        default["id"] = self.id
        definition = {"in": self.defined_in, "filename": str(self.filename)}
        if self.defined_in == "config":
            definition["config"] = self.raw_config
        default["definition"] = definition
        return {**default, **data}

    @classmethod
    def load_from_config_file(cls, data_stack, filename):
        config = YAML(typ="safe").load(filename.open("r"))
        type = config.pop("type", None)
        if type is None:
            raise ValueError("Missing required property `type`")
        cls = None
        if type is not None:
            if type == "libds.src.static.StaticTable":
                import libds.src.static

                cls = libds.src.static.StaticTable
            if type == "libds.src.google.GoogleSheet":
                import libds.src.google

                cls = libds.src.google.GoogleSheet
        if cls is None:
            raise ValueError(f"Don't know which source to use for type {type}")

        s = cls.from_config(config)
        s.defined_in = "config"
        s.raw_config = config
        s.filename = filename
        return s

    def update_config(self, config):
        if self.defined_in == "config":
            if "type" not in config:
                config["type"] = self.type
            with self.filename.open("wb") as file:
                yaml = YAML(typ="rt")
                yaml.dump(config, file)
        return BaseSource.load_from_config_file(
            self.data_stack, self.filename.resolve()
        )

    def _split_table_name(self):
        name = self._table_name
        if name is None:
            return "source", self.id
        else:
            m = re.match("^([^.]+)[.](.*)$", name)
            if m:
                return m[1], m[2]
            else:
                return "source", name

    @property
    def table_name(self):
        return self._split_table_name()[1]

    @property
    def schema_name(self):
        return self._split_table_name()[0]

    def load(self, recreate=False):
        return self.data_stack.store.append_records(
            schema_name=self.schema_name,
            table_name=self.table_name,
            records=self.collect_new_records(None),
            recreate=recreate,
        )

    def sample(self, limit=None, order_by=None):
        if order_by == "random":
            order_by = "random()"
        elif order_by == "new":
            order_by = "insid desc"
        elif order_by == "old":
            order_by = "insid asc"
        table = self.data_stack.store.get_table(self.schema_name, self.table_name)
        return table.sample(limit, order_by)


class StaticSource(BaseSource):
    def load(self, recreate=None):
        return super().load(recreate=recreate)
