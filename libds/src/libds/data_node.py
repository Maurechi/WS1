import json
import os
import sqlite3
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from pprint import pformat, pprint  # noqa: F401
from typing import Callable, Optional, Sequence

import psutil
import setproctitle

from libds.utils import _timedelta_as_info


class DataNodeState(Enum):
    STALE = "STALE"
    FRESH = "FRESH"
    EXPIRED = "EXPIRED"
    REFRESHING = "REFRESHING"
    REFRESHING_STALE = "REFRESHING_STALE"

    ORPHAN = "ORPHAN"


@dataclass
class DataNode:
    id: str
    container: Optional[str] = None
    upstream: Optional[Sequence[str]] = None
    details: Optional[dict] = None
    expires_after: Optional[timedelta] = None
    state: Optional[DataNodeState] = None
    refresher: Optional[Callable] = None

    def __post_init__(self):
        if self.upstream is None:
            self.upstream = []
        if isinstance(self.upstream, DataNode):
            self.upstream = [self.upstream]
        self.upstream = [u.id if isinstance(u, DataNode) else u for u in self.upstream]

    def info(self):
        i = {"id": self.id, "state": self.state.value}
        if self.container is not None:
            i["container"] = self.container
        if self.upstream:
            i["upstream"] = self.upstream
        if self.details:
            i["details"] = self.details
        if self.expires_after is not None:
            i["expires_after"] = _timedelta_as_info(self.expires_after)

        return i

    def refresh(self, orchestrator):
        self.refresher(orchestrator)

    def is_fresh(self):
        return self.state == DataNodeState.FRESH


class NoopDataNode(DataNode):
    def refresh(self, orchestrator):
        return None


class OrphanDataNode(DataNode):
    def __init__(self, id):
        super().__init__(id=id, state=DataNodeState.ORPHAN)

    def refresh(self, orchestrator):
        print(f"Not refreshing orphan node {self.id}.")


def _fetch_one_value(cursor, query, *args):
    return cursor.execute(query, *args).fetchone()[0]


class DataOrchestrator:
    def __init__(self, data_stack):
        self.data_stack = data_stack
        self.data_nodes = {}

    def _ensure_schema(self, conn):
        count = _fetch_one_value(
            conn.cursor(),
            "select count(*) from sqlite_master where type = 'table' and tbl_name = 'settings'",
        )
        if count == 0:
            cur = conn.cursor()
            cur.execute("begin")
            cur.execute("create table settings (key text, value text);")
            cur.execute("insert into settings (key, value) values ('version', '0')")
            conn.commit()

        cur = conn.cursor()
        version = _fetch_one_value(
            cur, "select value from settings where key = 'version'"
        )

        if version == "1":
            return

        if version == "0":
            cur = conn.cursor()
            cur.execute("begin")
            cur.execute(
                "create table tasks (tid text primary key, state text, info text)"
            )
            cur.execute(
                "create table data_nodes (nid text primary key, state text not null, current_tid text references tasks(tid) default null)"
            )
            cur.execute("update settings set value = '1' where key = 'version'")
            conn.commit()
            return

        raise Exception(f"Version {version} in orchestrator db.")

    def _connect(self):
        db_filename = self.data_stack.directory / "orchestrator.sqlite3"
        db_filename = db_filename.resolve()
        # print(f"Connecting to db at {db_filename}")
        return sqlite3.connect(db_filename, timeout=10)

    def connect(self):
        conn = self._connect()
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        foreign_keys = conn.execute("pragma foreign_keys;").fetchone()[0]
        if foreign_keys != 1:
            raise Exception("sqlite3 doesn't support foreign_keys. this is bad.")
        self._ensure_schema(conn)
        conn.close

        return self._connect()

    def collect_nodes(self, nodes):
        for node in nodes:
            if node.id in self.data_nodes:
                raise ValueError(
                    f"Attempting to add {node} with id {node.id} but {self.data_nodes[node.id]} already has that key."
                )
            self.data_nodes[node.id] = node

    def check_tasks(self):
        # TODO need to go and look for tasks whose pid is in the db but they don't exist, these are zombies and should be killed 20210408:mb
        return

    def load_states(self):
        conn = self.connect()
        nodes = self.data_nodes

        conn.execute("begin;")
        res = conn.execute("SELECT nid, state FROM data_nodes").fetchall()

        for id, state in res:
            if id in nodes:
                nodes[id].state = DataNodeState(state)
            else:
                nodes[id] = OrphanDataNode(id)

        for node in nodes.values():
            if node.state is None:
                node.state = DataNodeState.STALE
                conn.execute(
                    "insert into data_nodes (nid, state, current_tid) values (?, ?, null)",
                    [node.id, DataNodeState.STALE.value],
                )
        conn.commit()
        conn.close()

    def tick(self):
        ts = datetime.utcnow().isoformat() + "Z"
        log_dir = self.data_stack.directory / "logs" / f"{ts}-{uuid.uuid4()}"
        fork_and_check_for_zombies(self, log_dir)
        for node in self.data_nodes.values():
            if node.state == DataNodeState.STALE:
                if node.upstream is None:
                    raise Exception(f"no upstream list for {node.id}")

                fresh = [
                    nid in self.data_nodes and self.data_nodes[nid].is_fresh()
                    for nid in node.upstream
                ]

                if all(fresh):
                    fork_and_refresh(self, node, log_dir)

        return dict(log_dir=log_dir)

    def delete_node(self, node_id):
        node = self.data_nodes[node_id]
        info = node.info()

        with self.cursor() as cur:
            cur.execute("delete from data_nodes where nid = ?", [node_id])

        return info

    def downstream_nodes(self, node):
        downstream = {}
        for down in self.data_nodes.values():
            if node.id in down.upstream:
                downstream[down.id] = down

                for other in self.downstream_nodes(down):
                    downstream[other.id] = other

        return list(downstream.values())

    def set_node_state(self, node_id, state):
        node = self.data_nodes[node_id]
        if node.state == state:
            return

        if state == DataNodeState.STALE:
            downstream = [node] + self.downstream_nodes(node)
            downstream = [n.id for n in downstream]
            with self.cursor() as cur:
                cur.execute(
                    f"update data_nodes set state = 'STALE' where state = 'FRESH' and nid in ({ ','.join(['?'] * len(downstream)) })",
                    downstream,
                )
                cur.execute(
                    f"update data_nodes set state = 'REFRESHING_STALE' where state = 'REFRESHING' and nid in ({ ','.join(['?'] * len(downstream)) })",
                    downstream,
                )
        else:
            with self.cursor() as cur:
                cur.execute(
                    "update data_nodes set state = ? where nid = ?", [state, node_id]
                )

    @contextmanager
    def cursor(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("begin;")

        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def tasks(self):
        with self.cursor() as cur:
            res = cur.execute("select tid, state, info from tasks")
            return [
                Task(id=r[0], state=r[1], _info=json.loads(r[2]))
                for r in res.fetchall()
            ]

    def info(self):
        return dict(
            nodes=[node.info() for node in self.data_nodes.values()],
            tasks=[task.info() for task in self.tasks()],
        )


@dataclass
class Task:
    id: str
    state: str
    _info: object

    def info(self):
        i = dict(id=self.id, state=self.state, info=self._info.copy())
        for stream in ["stdout", "stderr"]:
            filename = i["info"].get(stream)
            contents = None
            if filename is not None:
                path = Path(filename)
                if path.exists():
                    try:
                        contents = path.open("r").read()
                    except Exception as e:
                        contents = f"_filename_to_log_contents: {e}\n"
                        contents += traceback.format_exc()
            if contents is None:
                i["info"].pop(stream)
            else:
                i["info"][stream] = contents

        return i


def fork():
    try:
        return os.fork()
    except OSError as err:
        print(f"{os.getpid()}: fork failed:", err, file=sys.stderr)
        raise err


class IsNotStale(Exception):
    pass


def _state_to_refreshing(orchestrator, nid, tid, info):
    with orchestrator.cursor() as cur:
        state = _fetch_one_value(
            cur, "select state from data_nodes where nid = ?", [nid]
        )
        if state == "STALE":
            cur.execute(
                "insert into tasks (tid, state, info) values (?, 'RUNNING', ?)",
                [
                    tid,
                    json.dumps(info),
                ],
            )
            cur.execute(
                "update data_nodes set state = ?, current_tid = ? where nid = ?",
                [DataNodeState.REFRESHING.value, tid, nid],
            )
        else:
            raise IsNotStale()


def timestamp():
    return datetime.utcnow().isoformat() + "Z"


def _task_complete(orchestrator, nid, tid):
    with orchestrator.cursor() as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ? and current_tid = ?",
            [DataNodeState.FRESH.value, nid, tid],
        )
        res = cur.execute("select info from tasks where tid = ?", [tid])
        info = json.loads(res.fetchone()[0])
        info["completed_at"] = timestamp()
        cur.execute(
            "update tasks set state = 'DONE', info = ? where tid = ?",
            [json.dumps(info), tid],
        )


def _task_failed(orchestrator, nid, tid, e, tb):
    with orchestrator.cursor() as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ?",
            [DataNodeState.STALE.value, nid],
        )
        info = _fetch_one_value(cur, "select info from tasks where tid = ?", [tid])
        info = json.loads(info)
        info["completed_at"] = timestamp()
        info["error"] = e
        info["traceback"] = tb
        cur.execute(
            "update tasks set state = 'ERRORED', info = ? where tid = ?",
            [json.dumps(info), tid],
        )


def trigger_refresh(orchestrator, node, info):
    print(f"Refresh on {node.id} triggered")
    pid = os.getpid()
    tid = datetime.utcnow().strftime("%Y%m%dT%H:%M:%S") + "-" + str(pid)

    info["pid"] = pid
    info["started_at"] = timestamp()
    info["nid"] = node.id

    while True:
        try:
            _state_to_refreshing(orchestrator, node.id, tid, info)
            break
        except sqlite3.OperationalError as oe:
            print(f"sqllite3.OperationalError: {oe}")
            time.sleep(1)
        except IsNotStale:
            print("is not stale. not refreshing.")
            return

    try:
        node.refresh(orchestrator)
        while True:
            try:
                _task_complete(orchestrator, node.id, tid)
                break
            except sqlite3.OperationalError as oe:
                print(f"OperationalError: {oe}")
                time.sleep(1)
    except Exception as e:
        print(f"{node.id} refresh error {e} setting back to stale")
        tb = traceback.format_exc()
        while True:
            try:
                _task_failed(orchestrator, node.id, tid, str(e), tb)
                break
            except sqlite3.OperationalError as oe:
                print(f"OperationalError: {oe}")
                time.sleep(1)
            except Exception as e:
                print(f"Exception: this is bad {e}")
                raise e

        print("Re raising exception")
        raise e
    finally:
        print("Exiting trigger_refresh")


# NOTE https://stackoverflow.com/questions/107705/disable-output-buffering 20210408:mb
class TaskOutputStream:
    def __init__(self, path):
        self.path = Path(path)
        self.stream = None
        self.start_at = None
        self.last_char = "\n"
        self.pid = f"{os.getpid():08}"

    def write(self, data):
        if self.stream is None:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o775)
            self.stream = self.path.open("w", buffering=1)
            self.start_at = time.time()
        e = self.elapsed()
        for c in data:
            if self.last_char == "\n":
                self.stream.write(self.pid + " " + e + " ")
            self.stream.write(c)
            self.last_char = c
        self.stream.flush()

    def writelines(self, lines):
        self.write("".join(lines))

    def flush(self):
        # flush can be called before `write`, so we need to handle the case where we haven't opened the stream yet.
        if self.stream is not None:
            self.stream.flush()

    def elapsed(self):
        e = int(time.time() - self.start_at)
        h = int(e / 3600)
        e = e % 3600
        m = int(e / 60)
        s = e % 60
        return f"{h:02}:{m:02}:{s:02}"

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def fork_and_refresh(orchestrator, node, log_dir):
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

    setproctitle.setproctitle(sys.argv[0] + " data-node-refresh " + node.id)

    sys.stdout = TaskOutputStream(stdout_file)
    sys.stderr = TaskOutputStream(stderr_file)

    pid_file.parent.mkdir(parents=True, exist_ok=True, mode=0o775)
    with pid_file.open("w") as file:
        print(str(os.getpid()), file=file)

    info = dict(stdout=str(stdout_file.resolve()), stderr=str(stderr_file.resolve()))
    trigger_refresh(orchestrator, node, info)

    if pid_file.exists():
        pid_file.unlink()

    sys.exit(0)


def check_for_zombies(orchestrator):
    with orchestrator.cursor() as cur:
        count = 0
        zombies = 0
        res = cur.execute("select tid, info from tasks where state = 'RUNNING'")
        for row in res.fetchall():
            count += 1
            tid = row[0]
            info = json.loads(row[1])
            if not psutil.pid_exists(info["pid"]):
                zombies += 1
                info["completed_at"] = timestamp()
                cur.execute(
                    "update tasks set state = 'ZOMBIE', info = ? where tid = ?",
                    [json.dumps(info), tid],
                )

        if zombies > 0:
            print(f"Found {zombies} zombie tasks out of {count} running")

            nodes = _fetch_one_value(
                cur,
                "select count(*) from data_nodes where current_tid in (select tid from tasks where state = 'ZOMBIE')",
            )
            print(f"{nodes} affected.")

            cur.execute(
                "update data_nodes set state = 'STALE', current_tid = null where current_tid in (select tid from tasks where state = 'ZOMBIE')"
            )


def fork_and_check_for_zombies(orchestrator, log_dir):
    with orchestrator.cursor() as cur:
        running = _fetch_one_value(
            cur, "select count(*) from tasks where state = 'RUNNING'"
        )
        if running == 0:
            return

    def log_file(suffix):
        return log_dir / ("check_for_zombies." + suffix)

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

    setproctitle.setproctitle(sys.argv[0] + " check-for-zombies")

    sys.stdout = TaskOutputStream(stdout_file)
    sys.stderr = TaskOutputStream(stderr_file)

    pid_file.parent.mkdir(parents=True, exist_ok=True, mode=0o775)
    with pid_file.open("w") as file:
        print(str(os.getpid()), file=file)

    check_for_zombies(orchestrator)

    if pid_file.exists():
        pid_file.unlink()

    sys.exit(0)
