import runpy
import traceback
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from libds.data_node import DataNode


class BaseModel:
    def __init__(
        self,
        id=None,
        filename=None,
        data_stack=None,
        table_name=None,
        schema_name=None,
        dependencies=None,
        tests=None,
    ):
        if data_stack is None:
            from libds.data_stack import CURRENT_DATA_STACK

            data_stack = CURRENT_DATA_STACK.value
        self.data_stack = data_stack

        self._init_properties(filename, id, table_name, schema_name)

        if dependencies is None:
            dependencies = []
        self.dependencies = dependencies
        if tests is None:
            tests = {}
        self.tests = tests

    @classmethod
    def from_file(cls, data_stack, filename):
        try:
            if filename.suffix == ".sql":
                return SQLModel.from_file(data_stack, filename)
            elif filename.suffix == ".py":
                return PythonModel.from_file(data_stack, filename)
        except Exception as e:
            return BrokenModel(
                data_stack, filename, exception=e, traceback=traceback.format_exc()
            )

    def _init_properties(self, filename, id, table_name, schema_name):
        self.filename = Path(filename)
        if id is None:
            id = filename.stem
        self.id = id
        if table_name is None:
            if filename is not None:
                table_name = filename.stem
        self.table_name = table_name

        if schema_name is None:
            schema_name = "public"
        self.schema_name = schema_name

    def info(self):
        filename = self.filename
        if filename is not None:
            filename = self.filename.relative_to(self.data_stack.directory)
        return dict(
            filename=str(filename),
            id=self.id,
            type=self.type,
            last_modified=self.last_modified(),
            source=filename.open().read(),
            table_name=self.table_name,
            schema_name=self.schema_name,
        )

    def fqid(self):
        return self.type + ":" + self.id

    def last_modified(self):
        if self.filename is None:
            return None
        return datetime.fromtimestamp(self.filename.stat().st_mtime)

    def update_id(self, id):
        new_filename = self.filename.with_name(id).with_suffix(self.filename.suffix)
        self.filename.rename(new_filename)
        self._init_properties(new_filename, id, None, None)
        return self

    def table(self):
        return self.data_stack.store.get_table(self.schema_name, self.table_name)

    def load_data_nodes(self):
        return [
            DataNode(
                refresher=lambda orchestrator: self.load_data(),
                id=self.schema_name + "." + self.table_name,
                container=self.fqid(),
                upstream=self.dependencies,
            )
        ]


def _ensure_schema(table_name):
    if "." in table_name:
        return table_name
    else:
        return "public." + table_name


class BrokenModel(BaseModel):
    def __init__(self, data_stack, filename, exception, traceback):
        super().__init__(data_stack=data_stack, filename=filename)
        self.type = "broken"
        self.exception = exception
        self.traceback = traceback

    def info(self):
        i = super().info()
        i.update(error=dict(exception=str(self.exception), traceback=self.traceback))
        return i


class SQLModel(BaseModel):
    def __init__(self, sql=None, type=None, **kwargs):
        super().__init__(**kwargs)
        self.sql = sql
        self.type = "sql"

    def info(self):
        i = super().info()
        i["sql"] = self.sql
        i["tests"] = {}
        for t in self.tests.keys():
            query = self.tests[t]
            failures = list(self.data_stack.store.execute_sql(query))
            i["tests"][t] = dict(ok=len(failures) == 0, failures=failures)

        return i

    @classmethod
    def from_file(cls, data_stack, filename):
        models_dir = data_stack.directory / "models"
        env = Environment(loader=FileSystemLoader([str(models_dir)]), autoescape=False)

        template = env.get_template(str(filename.relative_to(models_dir)))
        sql, config = data_stack.render_model_sql(template)
        is_query = config["is_query"]
        if is_query is None:
            is_query = not filename.stem.startswith("lib")
        cls = SQLQueryModel if is_query else SQLCodeModel
        return cls(
            data_stack=data_stack,
            filename=filename,
            sql=sql,
            table_name=config["table_name"],
            schema_name=config["schema_name"],
            dependencies=list(set(config["dependencies"])),
            tests=config["tests"],
        )

    def __repr__(self):
        return f"<{self.__class__.__module__}.{self.__class__.__name__} id={self.id}>"


class SQLQueryModel(SQLModel):
    def __init__(self, sql, **kwargs):
        super().__init__(sql, "select", **kwargs)

    def load_data(self):
        self.data_stack.store.create_or_replace_model(
            table_name=self.table_name, schema_name=self.schema_name, select=self.sql
        )

    @classmethod
    def create(cls, data_stack, id):
        return cls(
            data_stack=data_stack,
            filename=data_stack.models_dir() / f"{id}.sql",
            sql=None,
        )


class SQLCodeModel(SQLModel):
    def __init__(self, sql, **kwargs):
        super().__init__(sql, "sql", **kwargs)

    def load_data(self):
        self.data_stack.store.execute_sql(select=self.sql)

    def info(self):
        info = super().info()
        info.pop("table_name")
        info.pop("schema_name")
        return info


class PythonModel(BaseModel):
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.type = "python"

    @classmethod
    def from_file(cls, data_stack, filename):
        globals = runpy.run_path(filename)

        if "model" in globals:
            return cls(data_stack=data_stack, filename=filename, model=globals["model"])
        else:
            raise ValueError(f"No model function defined in {filename}")

    def load_data(self):
        self.model(self.data_stack)
