#!/usr/bin/env python
import functools
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from libds.__version__ import __version__
from libds.data_node import DataNodeState
from libds.data_stack import DataStack
from libds.model import PythonModel, SQLCodeModel, SQLQueryModel
from libds.source import BaseSource
from libds.utils import DoesNotExist, DSException


class OutputEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
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


class ClickCommand(click.Command):
    def __init__(self, *args, other_names=None, **kwargs):
        super().__init__(*args, **kwargs)
        if other_names is None:
            other_names = []
        self.other_names = other_names


class ClickGroup(click.Group):
    """This subclass of a group supports looking up aliases in a config
    file and with a bit of magic.
    """

    def get_command(self, ctx, cmd_name):
        # Step one: bulitin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        else:
            for name, cmd in self.commands.items():
                if cmd_name in cmd.other_names:
                    return self.get_command(ctx, name)
            else:
                return None

    def command(self, *args, **kwargs):
        return super().command(*args, cls=ClickCommand, **kwargs)


@click.group(cls=ClickGroup)
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


def command(**kwargs):
    def deco(cmd):
        @cli.command(**kwargs)
        @functools.wraps(cmd)
        def wrapped(*args, **kwargs):
            COMMAND.results(cmd(*args, **kwargs))

    return deco


@command()
def version():
    return {}


@command()
def info():
    return COMMAND.ds.info()


@command()
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


@command()
@click.argument("source_id")
def source_inspect(source_id):
    src = COMMAND.ds.get_source(source_id)
    return dict(info=src.info(), inspect=src.inspect())


@command()
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

    # NOTE this code, and the simliar logic in sources-update, belongs
    # in the data stack class. We need to make that class smarter and
    # this cli simpler. 20210410:mb

    if model_id != current_id:
        model = model.update_id(model_id)
    model.update_source(_arg_str(source))

    ds = COMMAND.reload_data_stack()
    orchestrator = ds.data_orchestrator
    model = ds.get_model(model_id)
    nodes = model.data_nodes()
    for n in nodes:
        orchestrator.set_node_state(n.id, DataNodeState.STALE)

    return COMMAND.reload_data_stack().get_model(model_id).info()


@command()
@click.argument("statement")
def execute(statement):
    statement = _arg_str(statement)
    try:
        return list(COMMAND.ds.store.execute(statement))
    except DSException as e:
        return {"error": e.as_json()}
    except Exception as e:
        return {"error": {"code": "error", "details": str(e)}}


@command()
def data_nodes():
    return COMMAND.ds.data_orchestrator.info()


@command(other_names=["dot"])
def data_orchestrator_tick():
    orchestrator = COMMAND.ds.data_orchestrator
    return orchestrator.tick()


@command(other_names=["dnu"])
@click.option(
    "--state",
    "-s",
    type=click.Choice(DataNodeState.__members__.keys(), case_sensitive=False),
    default=None,
)
@click.argument("node_id")
def data_node_update(node_id, state):
    if state is not None:
        state = DataNodeState[state]
        orchestrator = COMMAND.ds.data_orchestrator
        orchestrator.set_node_state(node_id, state)
        orchestrator.load_states()

    return orchestrator.info()


@command()
@click.argument("node_id")
def data_node_delete(node_id):
    orchestrator = COMMAND.ds.data_orchestrator
    orchestrator.delete_node(node_id)
    orchestrator.load_states()

    return orchestrator.info()


@command()
@click.pass_context
def help(ctx):
    click.echo(ctx.parent.get_help())


if __name__ == "__main__":
    cli()
