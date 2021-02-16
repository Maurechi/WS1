import os
import re
import sys
from pprint import pprint  # noqa: F401

import click
import google.auth
from google.cloud import resource_manager, secretmanager


def quote_name(name):
    def quote(m):
        code = ord(m[0])
        if code > 255:
            raise ValueError("Can't encode {char} in with 2 hex digits.")
        return "_{:02x}".format(code)

    return re.sub("[^a-zA-Z0-9]", quote, name)


def unquote_name(name):
    def unquote(m):
        return chr(int(m[1], base=16))

    return re.sub("_([0-9a-fA-F]{2})", unquote, name)


class SecretStore:
    def __init__(self, project_id=None):
        self.credentials, self.project_id = google.auth.default()
        if project_id is not None:
            self.project_id = project_id
        self.secret_manager = secretmanager.SecretManagerServiceClient(
            credentials=self.credentials
        )
        self.resource_manager = resource_manager.Client(credentials=self.credentials)

    @property
    def secrets(self):
        def _list(page_token):
            res = self.secret_manager.list_secrets(
                request={
                    "parent": f"projects/{self.project_id}",
                    "page_token": page_token,
                }
            )
            for s in res.secrets:
                yield Secret(store=self, resource=s.name)
            if res.next_page_token:
                yield from _list(res.next_page_token)

        return sorted(_list(None), key=lambda s: s.resource)

    def secret_from_name(self, name):
        return Secret(
            store=self,
            resource=f"projects/{self.project_id}/secrets/{quote_name(name)}",
        )


class SecretVersion:
    def __init__(self, store, resource):
        self.store = store
        self.resource = resource

    @property
    def raw_value(self):
        try:
            res = self.store.secret_manager.access_secret_version(
                request={"name": self.resource}
            )
            return res.payload.data
        except google.api_core.exceptions.NotFound:
            return None
        except google.api_core.exceptions.InvalidArgument:
            return None

    @property
    def value(self):
        raw = self.raw_value
        if raw is None:
            return None
        else:
            return raw.decode("utf-8")

    @property
    def exists(self):
        return self.value is not None


class Secret:
    def __init__(self, store=None, resource=None):
        self.store = store
        self.resource = resource

    def _ids(self):
        m = re.match(
            r"^projects/(?P<project_number>[^/]+)/secrets/(?P<secret_id>.*)$",
            self.resource,
        )
        if m:
            return (m.group("project_number"), m.group("secret_id"))
        else:
            return (None, None)

    @property
    def project_number(self):
        return self._ids()[0]

    @property
    def project_id(self):
        return self.store.resource_manager.fetch_project(self.project_number).name

    @property
    def secret_id(self):
        return self._ids()[1]

    @property
    def name(self):
        return unquote_name(self.secret_id)

    @property
    def exists(self):
        try:
            self.store.secret_manager.get_secret(request={"name": self.resource})
            return True
        except google.api_core.exceptions.NotFound:
            return False
        return True

    def create(self, exists_ok=True):
        if self.exists:
            if exists_ok:
                return self
            else:
                raise Exception(f"Secret {self.resource} already exists")
        self.store.secret_manager.create_secret(
            {
                "parent": f"projects/{self.project_id}",
                "secret_id": self.secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        return self

    def get_version(self, version):
        return SecretVersion(
            store=self.store, resource=f"{self.resource}/versions/{version}"
        )

    @property
    def value(self):
        return self.get_version("latest").value

    @value.setter
    def value(self, new_value):
        self.store.secret_manager.add_secret_version(
            request={
                "parent": self.resource,
                "payload": {"data": new_value.encode("utf-8")},
            }
        )
        return self.value


STORE = None


@click.group()
@click.option("-p", "--project-id", default=None)
def cli(project_id):
    global STORE
    STORE = SecretStore(project_id)


@cli.command()
def list():
    print(f"# In project {STORE.project_id}")
    for s in STORE.secrets:
        print(s.name)


@cli.command()
@click.argument("name")
@click.option("-v", "--version", default="latest")
@click.option("-r", "--raw", is_flag=True)
@click.pass_context
def get(ctx, name, version, raw):
    s = STORE.secret_from_name(name)
    if not s.exists:
        click.echo(f"No secret named {name}")
        ctx.exit(2)
    v = s.get_version(version)
    if not v.exists:
        click.echo(f"No version {name}:{version} found.")
        ctx.exit(2)
    if raw:
        with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as out:
            out.write(v.raw_value)
    else:
        print(v.value)


@cli.command()
@click.argument("name")
@click.argument("value")
@click.pass_context
def set(ctx, name, value):
    s = STORE.secret_from_name(name)
    if not s.exists:
        s.create()
    if value == "-":
        value = sys.stdin.read()
    s.value = value


if __name__ == "__main__":
    cli()
