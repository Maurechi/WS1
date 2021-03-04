#!/usr/bin/env python
import functools
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from libds import DataStack, __version__


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
@click.argument("source_id")
@click.argument("config")
def source_update(source_id, config):
    if config.strip() == "-":
        config = sys.stdin.read().strip()
    config = json.loads(config)
    source = COMMAND.ds.get_source(source_id)
    if source is None:
        return {"error": {"code": "source-not-found", "id": source_id}}
    else:
        source.update_config(config)
        return COMMAND.ds.get_source(source_id).info()


@command
@click.argument("source_id")
@click.option("-r", "--reload", is_flag=True, default=False)
def source_load(source_id, reload):
    return COMMAND.ds.get_source(source_id).load(reload)


@command
@click.argument("transformation_id")
@click.argument("source")
def transformation_update(transformation_id, source):
    trf = COMMAND.ds.get_trf(transformation_id)
    if trf is None:
        return {"error": {"code": "transformation-not-found", "id": id}}
    else:
        if source.strip() == "-":
            source = sys.stdin.read().strip()
        trf.update_source(source)
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
