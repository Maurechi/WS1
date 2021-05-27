import json
import re

from libds.data_node import DataNode
from libds.utils import yaml_load


class Record:
    def __init__(self, extracted_at=None, data=None, data_str=None):
        self.extracted_at = extracted_at
        self._data = data
        self._data_str = data_str

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


def _split_table_name(table_name):
    m = re.match("^([^.]+)[.](.*)$", table_name)
    if m:
        return m[1], m[2]
    else:
        return None, table_name


class BaseSource:
    def __init__(
        self,
        filename=None,
        id=None,
        data_stack=None,
        table=None,
    ):
        from libds.data_stack import (
            CURRENT_DATA_STACK,
            CURRENT_FILENAME,
            LOCAL_SOURCES,
        )

        if data_stack is None:
            data_stack = CURRENT_DATA_STACK.value
        self.data_stack = data_stack

        if filename is None:
            filename = CURRENT_FILENAME.value
        self.filename = filename.relative_to(self.data_stack.sources_dir())

        if id is None:
            id = self.filename.stem
        self.id = id

        if table is None:
            schema_name = "public"
            table_name = id
        else:
            schema_name, table_name = _split_table_name(table)
            if schema_name is None:
                schema_name = "public"
        self.schema_name = schema_name
        self.table_name = table_name

        LOCAL_SOURCES.append(self)

    @property
    def type(self):
        t = self.__class__.__module__ + "." + self.__class__.__name__
        return t.replace("/", "_")

    def fqid(self):
        return self.type + ":" + self.id

    def text(self):
        return (self.data_stack.sources_dir() / self.filename).open("r").read()

    def _info(self, **other_info):
        info = dict(info=other_info)
        info["type"] = self.type
        info["id"] = self.id
        info["filename"] = str(self.filename)
        if self.filename.suffix == ".py":
            info["code"] = self.text()
        elif self.filename.suffix == ".yaml":
            info["data"] = yaml_load(string=self.text())
        else:
            info["text"] = self.text()
        o = self.data_stack.data_orchestrator
        info["data_nodes"] = {}
        for node in self.data_nodes():
            node_state = o.load_node_state(node.id)
            node_id = node.id
            last_task = o.last_task_for_node(node_id)
            if last_task is not None:
                last_task = {
                    "id": last_task.id,
                    "state": last_task.state,
                    "started_at": last_task.started_at,
                    "completed_at": last_task.completed_at,
                }
            info["data_nodes"][node.id] = {
                "id": node.id,
                "state": node_state,
                "last_task": last_task,
            }
        return info

    def info(self):
        return self._info()

    def inspect(self):
        return {}

    @classmethod
    def class_from_yaml(cls, data_stack, path):
        config = yaml_load(string=path.open("r").read())
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
            if type == "libds.source.mysql.MySQL":
                import libds.source.mysql

                cls = libds.source.mysql.MySQL
        if cls is None:
            raise ValueError(
                f"Don't know which source to use for type {type} in {path}"
            )

        return cls

    def refresh(self):
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
                refresher=lambda o: self.refresh(),
            )
        ]


class BrokenSource(BaseSource):
    def __init__(self, data_stack, filename, error):
        super().__init__(
            data_stack=data_stack,
            id=None,
            filename=filename,
        )
        self.error = error
        self.data_stack = data_stack
        self._id = None

    @property
    def type(self):
        return ":broken"

    def info(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "type": self.type,
            "text": self.text(),
            "error": self.error,
        }

    def data_nodes(self):
        return []
