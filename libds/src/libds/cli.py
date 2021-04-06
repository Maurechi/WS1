#!/usr/bin/env python
import functools
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from libds import DataStack, __version__
from libds.model import PythonModel, SQLCodeModel, SQLQueryModel
from libds.orchestration import Orchestrator
from libds.source import BaseSource
from libds.utils import DependencyGraph, DoesNotExist, DSException


class OutputEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


@dataclass
class Command:
    directory = None
    format = None
    ds = None

    def __init__(self, directory, format):
        directory = Path(directory)
        self.directory = directory
        self.format = format
        self.ds = None
        if directory is not None:
            self.ds = DataStack.from_dir(directory)
            self.ds.load()

    def reload_data_stack(self):
        self.ds = DataStack.from_dir(self.ds.directory)
        self.ds.load()
        return self.ds

    def results(self, data):
        result = dict(meta=dict(version=__version__))
        if data is not None:
            if "error" in data and len(data) == 1:
                result["error"] = data["error"]
            else:
                result["data"] = data

        if self.format == "yaml":
            from ruamel.yaml import YAML

            yaml = YAML(typ="safe")
            yaml.dump(result, sys.stdout)
        elif self.format == "json":
            import json

            json.dump(result, sys.stdout, cls=OutputEncoder)
            print("")
        else:
            raise ValueError(f"Unknown format {self.format}")


def _arg_str(arg):
    if arg.strip() == "-":
        return sys.stdin.read().strip()
    else:
        return arg


def _arg_json(arg):
    return json.loads(_arg_str(arg))


COMMAND = None


@click.group()
@click.option(
    "-d",
    "--directory",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, allow_dash=False
    ),
    default=".",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="json",
)
def cli(directory, format):
    global COMMAND
    COMMAND = Command(directory, format)


def command(cmd):
    @cli.command()
    @functools.wraps(cmd)
    def wrapped(*args, **kwargs):
        COMMAND.results(cmd(*args, **kwargs))

    return wrapped


@command
def version():
    return {}


@command
def info():
    return COMMAND.ds.info()


@command
@click.option(
    "--if-exists",
    type=click.Choice(["error", "update"], case_sensitive=False),
    default="update",
)
@click.option(
    "--if-does-not-exist",
    type=click.Choice(["error", "create"], case_sensitive=False),
    default="create",
)
@click.option("--current-id")
@click.argument("id")
@click.argument("config")
def source_update(if_exists, if_does_not_exist, current_id, id, config):
    config = _arg_json(config)
    source = COMMAND.ds.get_source(id)
    if source is None:
        if if_does_not_exist == "error":
            return {"error": {"code": "source-not-found", "id": id}}
    else:
        if if_exists == "error":
            return {"error": {"code": "source-exists", "id": current_id}}

    if current_id is None:
        current_id = id
    BaseSource.update_config_file(
        data_stack=COMMAND.ds, current_id=current_id, id=id, config=config
    )
    return COMMAND.ds.get_source(id).info()


@command
@click.argument("source_id")
@click.option("-r", "--reload", is_flag=True, default=False)
def source_load(source_id, reload):
    src = COMMAND.ds.get_source(source_id)
    return src.load(reload)


@command
@click.argument("source_id")
def source_inspect(source_id):
    src = COMMAND.ds.get_source(source_id)
    return dict(info=src.info(), inspect=src.inspect())


@command
@click.option("--current-id")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["sql", "select", "python"], case_sensitive=False),
    default="select",
)
@click.option(
    "--if-exists",
    type=click.Choice(["error", "update"], case_sensitive=False),
    default="update",
)
@click.option(
    "--if-does-not-exist",
    type=click.Choice(["error", "create"], case_sensitive=False),
    default="create",
)
@click.argument("model_id")
@click.argument("source")
def model_update(model_id, type, if_exists, if_does_not_exist, current_id, source):
    if current_id is None:
        current_id = model_id
    try:
        model = COMMAND.ds.get_model(current_id)
        if if_exists == "error":
            return {"error": {"code": "model-exists", "id": current_id}}

    except DoesNotExist:
        if if_does_not_exist == "error":
            return {"error": {"code": "model-does-not-exist", "id": current_id}}

        if type == "select":
            cls = SQLQueryModel
        elif type == "sql":
            cls = SQLCodeModel
        elif type == "python":
            cls = PythonModel
        model = cls.create(data_stack=COMMAND.ds, id=current_id)

    if model_id != current_id:
        model = model.update_id(model_id)
    model.update_source(_arg_str(source))

    return COMMAND.reload_data_stack().get_model(model_id).info()


def model_load_one(model_id, reload):
    if reload:
        loading = "reloading"
    else:
        loading = "loading"
    print(f"{loading.capitalize()} {model_id}", file=sys.stderr, flush=True)
    sample = COMMAND.ds.get_model(model_id).load(reload).sample()
    # print(f"Done {loading} {model_id}", file=sys.stderr, flush=True)
    return sample


def _compute_model_load_order(model_ids):
    g = DependencyGraph()

    for m in COMMAND.ds.models:
        for dep in m.dependencies:
            g.edge(dep, m.id)

    return g.cascade_from_nodes(model_ids)


@command
@click.argument("model_id")
@click.option("-r", "--reload", is_flag=True, default=False)
@click.option(
    "--cascade",
    default="AFTER",
    type=click.Choice(["BEFORE", "BOTH", "AFTER"], case_sensitive=False),
)
@click.option("--no-cascade", is_flag=True, default=False)
@click.option("--wait/--no-wait", is_flag=True, default=False)
def model_load(model_id, reload, cascade, no_cascade, wait):
    m = COMMAND.ds.get_model(model_id)
    if m is None:
        return {"error": {"code": "model-not-found", "id": model_id}}

    if no_cascade:
        cascade = None
    load_task = m.load_task(reload=reload, cascade=cascade)
    o = Orchestrator(tasks=[load_task])
    o.execute(wait=wait)
    return {"job": {"id": o.id}}
    # return COMMAND.ds.get_model(model_id).table().sample()


@command
@click.option("-r", "--reload", is_flag=True, default=False)
@click.option("--wait/--no-wait", is_flag=True, default=False)
def model_load_all(reload, wait):
    o = Orchestrator(
        tasks=[
            model.load_task(reload=reload, cascade=True) for model in COMMAND.ds.models
        ]
    )
    o.execute(wait=wait)
    return {"job": {"id": o.id}}


@command
@click.argument("statement")
def execute(statement):
    statement = _arg_str(statement)
    try:
        return COMMAND.ds.store.execute(statement)
    except DSException as e:
        return {"error": e.as_json()}
    except Exception as e:
        return {"error": {"code": "error", "details": str(e)}}


@command
def data_nodes():
    return [node.info() for node in COMMAND.ds.data_nodes]


@command
@click.pass_context
def help(ctx):
    click.echo(ctx.parent.get_help())


if __name__ == "__main__":
    cli()
