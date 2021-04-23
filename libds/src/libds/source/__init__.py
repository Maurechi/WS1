import json
import re
from pathlib import Path

from libds.data_node import DataNode
from libds.utils import yaml_dump, yaml_load


class Record:
    def __init__(self, primary_key=None, data=None, valid_at=None, data_str=None):
        self.primary_key = primary_key
        self._data = data
        self._data_str = data_str
        self.valid_at = valid_at

    @property
    def data_str(self):
        if self._data_str is not None:
            return self._data_str
        elif self._data is not None:
            return json.dumps(self._data)
        else:
            return None

    @property
    def data(self):
        if self._data is not None:
            return self._data
        elif self._data_str is not None:
            return json.loads(self._data_str)
        else:
            return None


class BaseSource:
    def __init__(
        self,
        id=None,
        name=None,
        data_stack=None,
        defined_in="code",
        table_name=None,
    ):
        from libds.data_stack import (
            CURRENT_DATA_STACK,
            CURRENT_FILENAME,
            LOCAL_SOURCES,
        )

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
        t = self.__class__.__module__ + "." + self.__class__.__name__
        return t.replace("/", "_")

    @property
    def id(self):
        if self._id is None:
            if self.filename is None:
                return None
            else:
                return self.filename.stem
        else:
            return self._id

    def fqid(self):
        return self.type + ":" + self.id

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
        elif self.defined_in == "code":
            definition["code"] = self.filename.open("r").read()
        default["definition"] = definition
        return {**default, **data}

    def info(self):
        return self._info()

    def inspect(self):
        return {}

    @classmethod
    def load_from_config_file(cls, data_stack, filename):
        config = yaml_load(filename)
        type = config.pop("type", None)
        if type is None:
            raise ValueError("Missing required property `type`")
        cls = None
        if type is not None:
            if type == "libds.source.static.StaticTable":
                import libds.source.static

                cls = libds.source.static.StaticTable
            if type == "libds.source.google.GoogleSheet":
                import libds.source.google

                cls = libds.source.google.GoogleSheet
        if cls is None:
            raise ValueError(f"Don't know which source to use for type {type}")

        s = cls.from_config(config)
        s.defined_in = "config"
        s.raw_config = config
        s.filename = filename
        return s

    @classmethod
    def update_config_file(cls, data_stack, id, current_id, config):
        path = Path(data_stack.directory / "sources" / (id + ".yaml")).resolve()
        if current_id != id:
            current_path = Path(
                data_stack.directory / "sources" / (current_id + ".yaml")
            )
            current_path.rename(path)
        yaml_dump(config, path)
        return BaseSource.load_from_config_file(data_stack, path)

    def _split_table_name(self):
        name = self._table_name
        if name is None:
            return "public", self.id
        else:
            m = re.match("^([^.]+)[.](.*)$", name)
            if m:
                return m[1], m[2]
            else:
                return "public", name

    @property
    def table_name(self):
        return self._split_table_name()[1]

    @property
    def schema_name(self):
        return self._split_table_name()[0]

    def load(self):
        self.data_stack.store.load_raw_from_records(
            schema_name=self.schema_name,
            table_name=self.table_name + "_raw",
            records=self.collect_new_records(None),
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
    def data_nodes(self):
        return [
            DataNode(
                id=self.schema_name + "." + self.table_name + "_raw",
                container=self.fqid(),
                upstream=[],
                refresher=lambda o: self.load(),
            )
        ]
