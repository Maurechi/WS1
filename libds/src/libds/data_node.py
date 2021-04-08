import os
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pprint import pformat, pprint  # noqa: F401
from typing import Optional, Sequence

import arrow

from libds.utils import _timedelta_as_info


class DataNodeState(Enum):
    STALE = "STALE"
    FRESH = "FRESH"
    EXPIRED = "EXPIRED"
    REFRESHING = "REFRESHING"
    REFRESHING_STALE = "REFRESHING_STALE"


@dataclass
class DataNode:
    id: str
    container: Optional[str] = None
    inputs: Optional[Sequence[str]] = None
    details: Optional[dict] = None
    expires_after: Optional[timedelta] = None
    state: Optional[DataNodeState] = None

    def info(self):
        i = {"id": self.id, "state": self.state.value}
        if self.container is not None:
            i["container"] = self.container
        if self.inputs:
            i["inputs"] = self.inputs
        if self.details:
            i["details"] = self.details
        if self.expires_after is not None:
            i["expires_after"] = _timedelta_as_info(self.expires_after)

        return i

    def refresh(self, orchestrator):
        print(f"Refreshing {self.id}")
        import time

        time.sleep(10)
        print(f"Done {self.id}")


class DataOrchestrator:
    CONCURRENCY = 4

    def __init__(self, data_stack):
        self.data_stack = data_stack

    def _ensure_schema(self, conn):
        res = conn.execute(
            "select count(*) from sqlite_schema where type = 'table' and tbl_name = 'settings'"
        )
        count = res.fetchone()[0]
        if count == 0:
            cur = conn.cursor()
            cur.execute("create table settings (key text, value text);")
            cur.execute("insert into settings (key, value) values ('version', '0')")
            conn.commit()

        cur = conn.cursor()
        version = cur.execute("select value from settings where key = 'version'")
        version = version.fetchone()[0]

        if version == "1":
            return

        if version == "0":
            cur = conn.cursor()
            cur.execute("create table tasks (tid text primary key, state text)")
            cur.execute(
                "create table data_nodes (nid text primary key, state text not null, current_tid text references tasks(tid) default null)"
            )
            cur.execute("update settings set value = '1' where key = 'version'")
            conn.commit()
            return

        raise Exception(f"Version {version} in orchestrator db.")

    def connect(self):
        db_filename = self.data_stack.directory / "orchestrator.sqlite3"
        conn = sqlite3.connect(db_filename.resolve(), isolation_level=None)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        foreign_keys = conn.execute("pragma foreign_keys;").fetchone()[0]
        if foreign_keys != 1:
            raise Exception("sqlite3 doesn't support foreign_keys. this is bad.")
        self._ensure_schema(conn)
        return conn

    def load(self):
        self.load_states()

    def load_states(self):
        conn = self.connect()
        nodes = self.data_stack.data_nodes

        conn.execute("begin;")
        res = conn.execute("SELECT nid, state FROM data_nodes").fetchall()

        for id, state in res:
            nodes[id].state = DataNodeState(state)

        for node in self.data_stack.data_nodes.values():
            if node.state is None:
                node.state = DataNodeState.STALE
                conn.execute(
                    "insert into data_nodes (nid, state, current_tid) values (?, ?, null)",
                    [node.id, DataNodeState.STALE.value],
                )
        conn.commit()

    def tick(self):
        log_dir = self.data_stack.directory / "logs" / f"{arrow.get()}-{uuid.uuid4()}"
        nodes = self.data_stack.data_nodes
        for node in nodes.values():
            if node.state == DataNodeState.STALE:
                if node.inputs is None:
                    raise Exception(f"no inputs defined for {node.id}")
                if all(
                    [nodes[nid].state == DataNodeState.FRESH for nid in node.inputs]
                ):
                    fork_and_refresh(self, node, log_dir)


def fork():
    try:
        return os.fork()
    except OSError as err:
        print(f"{os.getpid()}: fork failed:", err, file=sys.stderr)
        raise err


@contextmanager
def connection(orchestrator):
    conn = orchestrator.connect()
    cur = conn.cursor()
    cur.execute("begin;")

    yield cur

    conn.commit()
    conn.close()


def trigger_refresh(orchestrator, node):
    with connection(orchestrator) as cur:
        state = cur.execute("select state from data_nodes where nid = ?", [node.id])
        state = state.fetchone()[0]
        if state == "STALE":
            tid = str(os.getpid())
            cur.execute("insert into tasks (tid, state) values (?, '{}')", [tid])
            cur.execute(
                "update data_nodes set state = ?, current_tid = ? where nid = ?",
                [DataNodeState.REFRESHING.value, tid, node.id],
            )

    try:
        node.refresh(orchestrator)

        with connection(orchestrator) as cur:
            cur.execute(
                "update data_nodes set state = ?, current_tid = null where nid = ? and current_tid = ?",
                [DataNodeState.FRESH.value, node.id, tid],
            )
            cur.execute("delete from tasks where tid = ?", [tid])
    except Exception as e:
        with connection(orchestrator) as cur:
            cur.execute(
                "update data_nodes set state = ?, current_tid = null where nid = ?",
                [DataNodeState.STALE.value, node.id],
            )
            cur.execute("delete from tasks where tid = ?", [tid])
        raise e


# NOTE https://stackoverflow.com/questions/107705/disable-output-buffering 20210408:mb
class TaskOutputStream:
    def __init__(self, path):
        self.stream = path.open("w")
        self.start_at = time.time()
        self.last_char = "\n"
        self.pid = f"{os.getpid():08}"

    def write(self, data):
        e = self.elapsed()
        for c in data:
            if self.last_char == "\n":
                self.stream.write(self.pid + " " + e + " ")
            self.stream.write(c)
            self.last_char = c
        self.stream.flush()

    def writelines(self, lines):
        self.write("".join(lines))

    def elapsed(self):
        e = int(time.time() - self.start_at)
        h = int(e / 3600)
        m = int(e / 60)
        s = e % 60
        return f"{h:02}:{m:02}:{s:02}"

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def fork_and_refresh(data_stack, node, log_dir):
    log_dir.mkdir(parents=True, exist_ok=True)

    def log_file(suffix):
        return log_dir / (node.id + "." + suffix)

    pid_file = log_file("pid")
    stdout_file = log_file("stdout")
    stderr_file = log_file("stderr")

    if fork() > 0:
        return pid_file

    # NOTE From this point on we're in the child and we never return 20210326:mb
    os.setsid()
    os.umask(0)

    if fork() > 0:
        sys.exit()

    sys.stdout = TaskOutputStream(stdout_file)
    sys.stderr = TaskOutputStream(stderr_file)

    with pid_file.open("w") as file:
        print(str(os.getpid()), file=file)

    trigger_refresh(data_stack, node)

    if pid_file.exists():
        pid_file.unlink()

    sys.exit(0)
