import json
import subprocess

import semver

from diaas.config import CONFIG


class LibDSException(Exception):
    pass


class LibDSRuntimeError(LibDSException):
    def __init__(self, cmd, stdout, stderr, returncode):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __str__(self):
        return (
            f"ds failed: {self.cmd} => {self.returncode}: {self.stderr}; {self.stdout}"
        )


class LibDSOutputParseError(LibDSException):
    pass


class LibDSVersionMismatch(LibDSException):
    pass


class LibDS:
    MIN_VERSION = semver.VersionInfo.parse("0.2.0")

    def __init__(self, path):
        self.path = path

    def call_ds(self, cmd, input=None):
        run = self.path / "run"
        venv = self.path / ".venv"
        if not (run.exists() and venv.exists()):
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
            raise LibDSRuntimeError(
                cmd=cmd, stdout=out, stderr=err, returncode=proc.returncode
            )
        try:
            response = json.loads(out)
        except Exception as e:
            raise LibDSOutputParseError(
                f"{e} while parsing ds response json: {cmd} => {out}"
            )
        meta = response.get("meta", {})
        meta_version = meta.get("version", "0.0.0")
        if self.MIN_VERSION <= meta_version:
            return response["data"]
        else:
            raise LibDSVersionMismatch(f"Wrong ds version: {meta_version}")

    def info(self):
        return self.call_ds(cmd=["info"])

    def source_update(self, id, current_id, config):
        cmd = "source-update --if-exists update --if-does-not-exist create".split()
        if current_id is not None:
            cmd += ["--current-id", current_id]
        cmd += [id, json.dumps(config)]
        return self.call_ds(cmd=cmd)

    def source_load(self, id):
        return self.call_ds(cmd=["source-load", id])

    def model_update(self, id, type=None, source=None, current_id=None):
        cmd = "model-update --if-exists update --if-does-not-exist create".split()
        if type is not None:
            cmd += ["--type", type]
        if current_id is not None:
            cmd += ["--current-id", current_id]
        cmd += [id, "-"]
        return self.call_ds(cmd=cmd, input=source)

    def model_load(self, id):
        return self.call_ds(cmd=["model-load", id])

    def execute(self, statement):
        return self.call_ds(cmd=["execute", "-"], input=statement)

    def jobs_list(self):
        return self.call_ds(cmd=["jobs-list"])
