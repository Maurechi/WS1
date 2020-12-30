import re
import os
import sys
from pprint import pprint  # noqa: F401

import click
import google.auth
from google.cloud import secretmanager
from google.cloud import resource_manager


class Secret:
    def __init__(self, client, secret):
        self.client = client
        self.secret = secret
        self.name = secret.name

    def list_versions(self, page_token=None):
        res = self.client.secret_manager.list_secret_versions(
            request={"parent": self.name, "page_token": page_token}
        )
        for v in res.versions:
            yield Version(secret=self, name=v.name)
        if res.next_page_token:
            yield from self.list_versions(res.next_page_token)

    @property
    def versions(self):
        return self.list_versions()

    @property
    def display_name(self):
        m = re.match(r'^projects/(?P<project_number>[^/]+)/secrets/(?P<secret_id>.*)$', self.name)
        if m:
            project_id = self.client.project_id(m.group("project_number"))
            secret_id = m.group("secret_id")
            return project_id + "/" + secret_id
        else:
            return self.name

    def get_version(self, version):
        return Version(secret=self, name=self.name + "/versions/" + version)

    def add_version(self, value):
        res = self.client.secret_manager.add_secret_version(
            request={"parent": self.name, "payload": {"data": value.encode("utf-8")}}
        )
        return Version(secret=self, name=res.name)


class Version:
    def __init__(self, secret, name):
        self.secret = secret
        self.name = name

    @property
    def value(self):
        try:
            res = self.secret.client.secret_manager.access_secret_version(
                request={"name": self.name}
            )
        except google.api_core.exceptions.NotFound:
            return None
        except google.api_core.exceptions.InvalidArgument:
            return None
        return res.payload.data


class Client:
    def __init__(self):
        self.credentials, self.project = google.auth.default()
        self.secret_manager = secretmanager.SecretManagerServiceClient( credentials=self.credentials )
        self.resource_manager = resource_manager.Client(credentials=self.credentials)

    def list_secrets(self, page_token=None):
        res = self.secret_manager.list_secrets(
            request={"parent": f"projects/{self.project}", "page_token": page_token}
        )
        for s in res.secrets:
            yield Secret(client=self, secret=s)
        if res.next_page_token:
            yield from self.list_secrets(self.project, res.next_page_token)

    @property
    def secrets(self):
        return self.list_secrets()

    def get_secret(self, secret_id):
        try:
            res = self.secret_manager.get_secret(
                request={"name": f"projects/{self.project}/secrets/{secret_id}"}
            )
        except google.api_core.exceptions.NotFound:
            return None
        return Secret(self, res)

    def create_secret(self, secret_id):
        self.secret_manager.create_secret({
            "parent": f"projects/{self.project}",
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        })
        return self.get_secret(secret_id)

    def project_id(self, project_number):
        return self.resource_manager.fetch_project(project_number).name

    def project_number(self, project_id):
        prj = resource_manager.project.Project(project_id=project_id)
        prj.reload()
        return prj.project_number


@click.group()
def cli():
    pass


@cli.command()
def list():
    client = Client()
    for s in client.secrets:
        print(s.display_name)


@cli.command()
@click.argument("secret_id")
@click.option("-v", "--version", default="latest")
@click.option("-r", "--raw", is_flag=True)
@click.pass_context
def get(ctx, secret_id, version, raw):
    client = Client()
    s = client.get_secret(secret_id)
    if s is None:
        click.echo(f"No secret named {secret_id}")
        ctx.exit(2)
    value = s.get_version(version).value
    if value is None:
        click.echo(f"No secret names {secret_id}:{version} found.")
        ctx.exit(2)
    if raw:
        with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as out:
            out.write(value)
    else:
        print(value.decode("utf-8"))


@cli.command()
@click.argument("secret_id")
@click.argument("value")
@click.pass_context
def set(ctx, secret_id, value):
    client = Client()
    s = client.get_secret(secret_id)
    if s is None:
        s = client.create_secret(secret_id)
    version = s.add_version(value)
    print(version.name)


if __name__ == '__main__':
    cli()
