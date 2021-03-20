import runpy
from datetime import datetime
from itertools import chain
from pathlib import Path
from pprint import pformat

from jinja2 import Environment, FileSystemLoader

from libds.utils import ThreadLocalValue

CURRENT_DATA_STACK = ThreadLocalValue()


def load_models(data_stack):
    sqls = data_stack.models_dir.glob("**/*.sql")
    pys = data_stack.models_dir.glob("**/*.py")
    models = [
        BaseModel.from_file(data_stack, filename) for filename in chain(sqls, pys)
    ]
    return filter(None, models)


class BaseModel:
    def __init__(
        self,
        id=None,
        filename=None,
        data_stack=None,
        table_name=None,
        schema_name=None,
        dependencies=None,
    ):
        if data_stack is None:
            data_stack = CURRENT_DATA_STACK.value
        self.data_stack = data_stack

        self._init_properties(filename, id, table_name, schema_name)

        if dependencies is None:
            dependencies = []
        self.dependencies = dependencies

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

    def last_modified(self):
        if self.filename is None:
            return None
        return datetime.fromtimestamp(self.filename.stat().st_mtime)

    def update_source(self, source):
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with self.filename.open("wb") as file:
            file.write(source.encode("utf-8"))
        return self.__class__.from_file(self.data_stack, self.filename)

    def update_id(self, id):
        new_filename = self.filename.with_name(id).with_suffix(self.filename.suffix)
        self.filename.rename(new_filename)
        self._init_properties(new_filename, id, None, None)
        return self

    @classmethod
    def from_file(cls, data_stack, filename):
        if filename.suffix == ".sql":
            return SQLModel.from_file(data_stack, filename)
        elif filename.suffix == ".py":
            return PythonModel.from_file(data_stack, filename)


def _pprint_call(func, **args):
    str = func + "("
    str += ", ".join([key + "=" + pformat(args[key]) for key in sorted(args.keys())])
    str += ")"
    str = str.replace("\n", "")
    str = "/* " + str + " */"
    return str


class SQLModel(BaseModel):
    def __init__(self, sql=None, type=None, **kwargs):
        super().__init__(**kwargs)
        self.sql = sql
        self.type = "sql"

    def info(self):
        return {**super().info(), "sql": self.sql}

    @classmethod
    def from_file(cls, data_stack, filename):
        models_dir = data_stack.directory / "models"
        env = Environment(loader=FileSystemLoader([str(models_dir)]), autoescape=False)

        template = env.get_template(str(filename.relative_to(models_dir)))
        config = dict(
            dependencies=[],
            table_name=None,
            schema_name=None,
            is_query=not filename.stem.startswith("lib"),
        )

        def depends_on(model_id, *other_deps):
            config["dependencies"] += [model_id] + list(other_deps)
            return model_id

        def table_name(table, schema=None):
            if table is not None:
                config["table_name"] = table
            if schema is not None:
                config["schema_name"] = schema
            return _pprint_call("table_name", table=table, schema=schema)

        def is_query():
            config["is_query"] = True

        def is_statement():
            config["is_query"] = False

        sql = template.render(
            depends_on=depends_on,
            table_name=table_name,
            is_query=is_query,
            is_statement=is_statement,
        )
        if config["is_query"]:
            cls = SQLQueryModel
        else:
            cls = SQLCodeModel
        return cls(
            data_stack=data_stack,
            filename=filename,
            sql=sql,
            table_name=config["table_name"],
            schema_name=config["schema_name"],
            dependencies=config["dependencies"],
        )


class SQLQueryModel(SQLModel):
    def __init__(self, sql, **kwargs):
        super().__init__(sql, "select", **kwargs)

    def load(self, reload):
        self.data_stack.store.create_or_replace_model(
            table_name=self.table_name, schema_name=self.schema_name, select=self.sql
        )
        return self.data_stack.store.get_table(self.schema_name, self.table_name)

    @classmethod
    def create(cls, data_stack, id):
        return cls(
            data_stack=data_stack,
            filename=data_stack.models_dir / f"{id}.sql",
            sql=None,
        )


class SQLCodeModel(SQLModel):
    def __init__(self, sql, **kwargs):
        super().__init__(sql, "sql", **kwargs)

    def load(self, reload):
        store = self.data_stack.store
        store.execute_sql(select=self.sql)
        return store.get_table(self.schema_name, self.table_name).sample()

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
        CURRENT_DATA_STACK.value = data_stack
        globals = runpy.run_path(filename)
        CURRENT_DATA_STACK.value = None

        if "model" in globals:
            return cls(data_stack=data_stack, filename=filename, model=globals["model"])
        else:
            raise ValueError(f"No model function defined in {filename}")

    def load(self, reload):
        return self.model(self.data_stack.store)
