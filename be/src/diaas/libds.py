import json
import subprocess

import semver


class LibDS:
    MIN_VERSION = semver.VersionInfo.parse("0.2.0")

    def __init__(self, path):
        self.path = path

    def call_ds(self, cmd, input=None):
        real_args = []
        for a in cmd:
            if isinstance(a, str):
                real_args.append(a)
            else:
                real_args.extend(a)
        cmd = [str(self.path / "run"), "ds", "-f", "json"] + real_args
        proc = subprocess.Popen(
            cmd,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate(input=input)
        if proc.returncode > 0:
            raise Exception(f"ds failed: {cmd} => {proc.returncode}: {err}; {out}")
        try:
            response = json.loads(out)
        except Exception as e:
            raise Exception(f"{e} while parsing ds response json: {cmd} => {out}")
        meta = response.get("meta", {})
        meta_version = meta.get("version", "0.0.0")
        if self.MIN_VERSION <= meta_version:
            return response["data"]
        else:
            raise ValueError(f"Wrong ds version: {meta_version}")

    def info(self):
        return self.call_ds(cmd=["info"])

    def update_source_config(self, id, config):
        return self.call_ds(
            cmd=["update-source-config", id, "-"], input=json.dumps(config)
        )

    def load_source(self, id):
        return self.call_ds(cmd=["load-source", id])
