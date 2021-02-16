import os

import click
from diaas_ops.configure.configuration import Configuration


@click.command()
@click.option(
    "--format",
    "-f",
    default="bash",
    type=click.Choice("json table bash fish env docker".split()),
)
@click.option("--with-be/--without-be", default=True)
@click.option("--with-fe/--without-fe", default=True)
@click.option("--trailing-newline/--no-trailing-newline", default=True)
@click.option(
    "--install-dir",
    default=None,
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
)
@click.argument("environment", default=None, type=str, required=False)
def cli(environment, format, install_dir, with_be, with_fe, trailing_newline):
    """Export bash code to set env vars configuring the given env and version."""
    if environment is not None:
        os.environ["DIAAS_DEPLOYMENT_ENVIRONMENT"] = environment
    if "DIAAS_DEPLOYMENT_ENVIRONMENT" not in os.environ:
        raise click.ClickException("ENVIRONMENT not specified.")
    Configuration(install_dir=install_dir, with_be=with_be, with_fe=with_fe).print_as(
        format,
        trailing_newline=trailing_newline
    )


if __name__ == "__main__":
    cli()
