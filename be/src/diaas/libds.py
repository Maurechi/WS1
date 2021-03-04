import json
import subprocess

import semver

from diaas.config import CONFIG


class LibDS:
    MIN_VERSION = semver.VersionInfo.parse("0.2.0")

    def __init__(self, path):
        self.path = path

    def call_ds(self, cmd, input=None):
        run = self.path / "run"
        if not run.exists():
            script = CONFIG.BE_BIN_DIR / "bootstrap-data-stack"
            subprocess.check_call([str(script)], cwd=self.path)

        real_args = []
        for a in cmd:
            if isinstance(a, str):
                real_args.append(a)
            else:
                real_args.extend(a)
        cmd = [str(run), "ds", "-f", "json"] + real_args
        proc = subprocess.Popen(
            cmd,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.path,
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

    def source_update(self, id, config):
        return self.call_ds(cmd=["source-update", id, "-"], input=json.dumps(config))

    def source_load(self, id):
        return self.call_ds(cmd=["source-load", id])

    def transformation_update(self, id, source):
        return self.call_ds(cmd=["transformation-update", id, "-"], input=source)

    def transformation_load(self, id):
        return self.call_ds(cmd=["transformation-load", id])
