import json
import subprocess

import semver


class LibDS:
    def __init__(self, path):
        self.path = path

    def info(self):
        info_text = subprocess.check_output(
            [str(self.path / "run")] + "ds -f json info".split()
        )
        response = json.loads(info_text)
        __version = response.get("__", {}).get("version", "0.0.0")
        __version = semver.VersionInfo.parse(__version)
        if __version >= "0.2.0":
            return response
        else:
            raise ValueError(f"Wrong ds version: {__version}")

    def update_source_config(self, id, config):
        cmd = (
            [str(self.path / "run")]
            + "ds -f json update-source-config".split()
            + [id, "-"]
        )
        update = subprocess.Popen(
            cmd,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = update.communicate(input=json.dumps(config))
        if update.returncode > 0:
            raise Exception(f"ds failed: {cmd} => {update.returncode}: {err}; {out}")
        try:
            response = json.loads(out)
        except Exception as e:
            raise Exception(f"Failed to parse '{out}' as json: {e}. Call was {cmd}")
        __version = response.pop("__", {}).get("version", "0.0.0")
        __version = semver.VersionInfo.parse(__version)
        if __version >= "0.2.0":
            return response
        else:
            raise ValueError(f"Wrong ds version: {__version}")
