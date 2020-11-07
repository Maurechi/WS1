import sys
from pathlib import Path
import _sh
import click
from configuration import Configuration


@click.command()
@click.option("-r", "--recreate", default=False, is_flag=True)
@click.argument("up_args", nargs=-1)
def main(recreate, up_args):
    _sh.env.DIAAS_UID = _sh.output("id -u")
    _sh.env.DIAAS_GID = _sh.output("id -g")
    Configuration(environment="lcl").inject_into_environ()

    ROOT = str(Path(__file__).parent.parent.parent)
    DOCKER_COMPOSE = f"""
        docker-compose
        -p diaas_{_sh.env.DIAAS_DEPLOYMENT_BRANCH}_{_sh.env.DIAAS_DEPLOYMENT_ENVIRONMENT}
        -f ./ops/lcl/docker-compose.yaml
    """.split()
    if recreate:
        _sh.call(DOCKER_COMPOSE + "down -v --rmi local".split(), cwd=ROOT)
    _sh.call(DOCKER_COMPOSE + "build --parallel".split())
    _sh.exec(DOCKER_COMPOSE + ["up"] + list(up_args), cwd=ROOT)


if __name__ == "__main__":
    sys.stdout.flush()
    main()
