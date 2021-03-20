#!/usr/bin/env python
import functools
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from libds import DataStack, __version__
from libds.src import BaseSource
from libds.trf import (
    PythonTransformation,
    SQLCodeTransformation,
    SQLQueryTransformation,
)


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
        if directory is not None:
            self.ds = DataStack.from_dir(directory)

    def results(self, data):
        result = dict(meta=dict(version=__version__))
        if data is not None:
            result.update(dict(data=data))

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
    default="yaml",
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
@click.argument("transformation_id")
@click.argument("source")
def transformation_update(
    transformation_id, type, if_exists, if_does_not_exist, current_id, source
):
    if current_id is None:
        current_id = transformation_id
    trf = COMMAND.ds.get_trf(current_id)
    if trf is None:
        if if_does_not_exist == "error":
            return {
                "error": {"code": "transformation-does-not-exist", "id": current_id}
            }

        if type == "select":
            cls = SQLQueryTransformation
        elif type == "sql":
            cls = SQLCodeTransformation
        elif type == "python":
            cls = PythonTransformation
        trf = cls.create(data_stack=COMMAND.ds, id=current_id)

    if trf is not None:
        if if_exists == "error":
            return {"error": {"code": "transformation-exists", "id": current_id}}

    trf.update_source(_arg_str(source))
    if transformation_id != current_id:
        trf = trf.update_id(transformation_id)
    return COMMAND.ds.get_trf(transformation_id).info()


@command
@click.argument("transformation_id")
@click.option("-r", "--reload", is_flag=True, default=False)
def transformation_load(transformation_id, reload):
    return COMMAND.ds.get_trf(transformation_id).load(reload)


@command
@click.pass_context
def help(ctx):
    click.echo(ctx.parent.get_help())


if __name__ == "__main__":
    cli()
