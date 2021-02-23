import datetime
import json
import os
import shlex
import sys
from pathlib import Path

import pygit2
import tabulate


def from_env(name, type=None, default=None, required=None):
    if type is None:
        type = str
    if required is None:
        required = False
    raw_value = os.environ.get(name, None)
    if raw_value is None:
        if required:
            raise ValueError(f"Required var {name} not found in env.")
        else:
            return default
    elif type == str:
        return raw_value
    elif type == int:
        return int(raw_value)
    elif type == bool:
        if default is None:
            default = False
        if default is False:
            return raw_value.lower() in ["true", "yes", "on", "enabled", "1"]
        else:
            return raw_value.lower() in ["false", "no", "off", "disabled", "0"]
    elif type == Path:
        return Path(raw_value)
    else:
        raise ValueError(f"Unknown type {type}")


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        else:
            super().default(o)


class BaseConfiguration:
    def __init__(self, with_fe=True, with_be=True, environment=None):
        self.values = {}
        self.with_fe = with_fe
        self.with_be = with_be

        self.timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        if environment is None:
            environment = from_env("DIAAS_DEPLOYMENT_ENVIRONMENT", required=True)
        if environment in ["prd", "stg", "lcl"]:
            self.environment = environment
            self._set("DIAAS_DEPLOYMENT_ENVIRONMENT", value=self.environment)
        else:
            raise ValueError(
                f"Unknown environment {environment}, must be one of prd, stg, or lcl."
            )

    def _set(self, key, value=None, type=None, default=None, required=False):
        if value is None:
            value = from_env(key, type=type, default=default, required=required)
        self.values[key] = value
        return value

    def _set_all(self, **kwargs):
        for key, value in kwargs.items():
            self.values[key] = from_env(key, default=value)

    @property
    def branch(self):
        if self.is_stg:
            branch = pygit2.Repository(".").head.shorthand
        else:
            branch = self.if_env(prd="master", lcl="HEAD")
        return from_env("DIAAS_DEPLOYMENT_BRANCH", default=branch)

    @property
    def is_prd(self):
        return self.environment == "prd"

    @property
    def is_stg(self):
        return self.environment == "stg"

    @property
    def is_lcl(self):
        return self.environment == "lcl"

    def if_env(self, **env_values):
        for e, value in env_values.items():
            if self.environment == e:
                return value
        if "otherwise" in env_values:
            return env_values["otherwise"]
        else:
            return None

    @property
    def is_master(self):
        return self.branch == "master"

    def _values_as_strings(self):
        values = {}
        for k, v in self.values.items():
            if v is not None:
                if isinstance(v, bool):
                    v = "true" if v else "false"
                else:
                    v = str(v)
                values[k] = v
        return values

    def _values_for_shell(self):
        values = {}
        for k, v in self._values_as_strings().items():
            try:
                quoted_value = shlex.quote(v)
            except Exception as e:
                raise ValueError(f"Failure quoting value `{v}` (from `{dict[k]}`): {e}")
            try:
                quoted_key = shlex.quote(k)
            except Exception as e:
                raise ValueError(f"Failure quoting key `{k}`: {e}")
            values[quoted_key] = quoted_value
        return values

    def print_as(self, format, fp=sys.stdout, trailing_newline=True):
        if format == "json":
            text = json.dumps(self.values, sort_keys=True, cls=JSONEncoder)
        elif format == "table":
            values = self._values_for_shell()
            table = [[key, values[key]] for key in sorted(values.keys())]
            text = tabulate.tabulate(table)
        else:
            values = self._values_for_shell()
            lines = []
            for key in sorted(values.keys()):
                value = values[key]
                if format == "bash":
                    lines.append(f"export {key}={value}")
                elif format == "fish":
                    lines.append(f"set -x {key} {value}")
                elif format == "env":
                    lines.append(f"{key}={value}")
                elif format == "docker":
                    lines.append(f"-e {key}={value}")
                else:
                    raise ValueError(f"Bad format {format}")
            if format in ["env", "docker"]:
                text = " ".join(lines)
            else:
                text = "\n".join(lines)
        if text:
            print(text, file=fp, end="\n" if trailing_newline else "")

    def inject_into_environ(self):
        os.environ.update(self._values_as_strings())
        return os.environ
