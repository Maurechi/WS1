import json
import sys
import tabulate
import datetime
import shlex
import os
import slugify


def from_env(name, type=str, default=None, required=False):
    raw_value = os.environ.get(name, None)
    if raw_value is None:
        if required:
            raise ValueError(f"Required var {name} not found in env.")
        else:
            return default
    elif type == str:
        return raw_value
    elif type == int:
        return int(str)
    elif type == bool:
        if default is None:
            default = False
        if default is False:
            return raw_value.lower() in ["true", "yes", "on", "enabled", "1"]
        else:
            return raw_value.lower() in ["false", "no", "off", "disabled", "0"]
    else:
        raise ValueError(f"Unknown type {type}")


def _values_for_shell(dict):
    values = {}
    for k, v in dict.items():
        if v is None:
            continue
        if isinstance(v, bool):
            v = "true" if v else "false"
        else:
            v = str(v)

        try:
            quoted_value = shlex.quote(v)
        except Exception as e:
            raise ValueError(f"Failure quoting `{v}` (from `{dict[k]}`): {e}")
        values[k] = quoted_value

    return values


class BaseConfiguration:
    def __init__(self, with_fe=True, with_be=True):
        self.with_fe = with_fe
        self.with_be = with_be
        self.values = {}
        self.timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    def _set(self, **kwargs):
        keys = list(kwargs.keys())
        if len(keys) != 1:
            raise Exception("Wrong number of arguments to _set")
        self._set_all(**kwargs)
        return self.values[keys[0]]

    def _set_all(self, **kwargs):
        for key, value in kwargs.items():
            self.values[key] = value

    @property
    def branch(self):
        branch = self.if_env(prd="master", stg="master", lcl="HEAD")
        return from_env("DIAAS_DEPLOYMENT_BRANCH", default=branch)

    @property
    def environment(self):
        e = from_env("DIAAS_DEPLOYMENT_ENVIRONMENT", required=True)
        if e in ["prd", "stg", "lcl"]:
            return e
        else:
            raise ValueError(
                f"Unknown environment {e}, must be one of prd, stg, or lcl."
            )

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

    def print_as(self, format, fp=sys.stdout):
        if format == "json":
            text = json.dumps(self.values, sort_keys=True)
        elif format == "table":
            values = _values_for_shell(self.values)
            table = [[key, values[key]] for key in sorted(values.keys())]
            text = tabulate.tabulate(table)
        else:
            values = _values_for_shell(self.values)
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
            print(text, file=fp)
