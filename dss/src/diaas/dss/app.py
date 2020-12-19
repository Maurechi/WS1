import json
import sys
import traceback
from pprint import pformat, pprint  # noqa: F401

import click
import yaml
from flask import Flask, current_app, jsonify, request
from flask.cli import AppGroup

from diaas.dss.data_stack import DataStack

app = Flask(__name__)


class ValidationError(Exception):
    pass


class MissingRequiredProperty(ValidationError):
    def __init__(self, property, payload):
        super().__init__(f"Property '{property}' not found in {pformat(payload)}")


@app.errorhandler(Exception)
def base_error_handler(e):
    bt = traceback.format_exc()
    print(bt, file=sys.stderr)
    return jsonify(dict(e=repr(e), traceback=traceback.format_exc())), 500


class Request:
    def __init__(self):
        self.request = request
        # NOTE this is intentionaly breaking some security around
        # flask's handling of json input (not requiring the
        # application type to be json). we're assuming this is
        # never called from untrusted sources (either locally, in
        # which case all bets are off, or via the bacend, which we
        # assume has parsed the client input and generated a clean
        # payload) 20201219:mb
        data = request.get_data(as_text=True)
        if data:
            self.json = request.get_json(force=True)
        else:
            self.json = {}

    def get(self, name, required=True, default=None, type=str):
        val = self.json.get(name, self)
        if val is self:
            if required:
                raise MissingRequiredProperty(name, self.json)
            else:
                val = default
        if type == str:
            return val
        if type == int:
            return int(val)
        if type == bool:
            if val in [True, False]:
                return val
            else:
                raise ValidationError(
                    f"Property {name}'s value '{val}' is not a boolean."
                )
        raise ValueError(f"Unknown value type {type}")


@app.route("/", methods=["POST"])
def initialize_data_stack():
    req = Request()
    directory = req.get("directory", required=True)
    force = req.get("force", default=False, type=bool)

    DataStack(directory).initialize(force=force)

    return jsonify(dict(ok=True)), 200


@app.route("/modules/", methods=["GET"])
def get_modules():
    return jsonify([]), 200


dss_cli = AppGroup("dss")
app.cli.add_command(dss_cli)


@dss_cli.command("req")
@click.argument("method")
@click.argument("endpoint")
@click.option("-d", "--data", type=str)
def req(method, endpoint, data):
    app = current_app
    app.config["TESTING"] = True
    if data:
        data = json.dumps(yaml.safe_load(data))
    else:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
        else:
            data = ""

    with app.test_client() as client:
        method = method.upper()
        endpoint = "/" + endpoint.lstrip("/")
        res = client.open(
            method=method, path=endpoint, follow_redirects=True, data=data
        )
        out = dict(
            status_code=res.status_code,
            status=res.status,
            headers=dict(res.headers),
            body=res.json,
        )
        print(json.dumps(out))
