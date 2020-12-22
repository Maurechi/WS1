from pprint import pformat, pprint  # noqa: F401

import click

from diaas_dss.data_stack import DataStack


@click.group()
def cli():
    pass


@cli.command("init")
@click.argument("directory")
@click.option("-f", "--force", is_flag=True, default=False)
def init(directory, force):
    DataStack(directory).initialize(force=force)


@cli.command("clone")
@click.argument("origin")
@click.argument("directory")
@click.option("-f", "--force", is_flag=True, default=False)
def clone(force, origin, directory):
    DataStack(origin).clone(directory, force=force)
