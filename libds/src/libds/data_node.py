import json
import os
import sqlite3
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from pprint import pformat, pprint  # noqa: F401
from typing import Callable, Optional, Sequence, Union

import arrow
import psutil
import setproctitle

from libds.utils import parse_timedelta


class DataNodeState(Enum):
    STALE = "STALE"
    FRESH = "FRESH"
    EXPIRED = "EXPIRED"
    REFRESHING = "REFRESHING"
    REFRESHING_STALE = "REFRESHING_STALE"

    ORPHAN = "ORPHAN"


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

        if version == "2":
            pass

        elif version == "1":
            cur = conn.cursor()
            cur.execute("begin")
            cur.execute("alter table tasks add column nid text;")
            cur.execute("alter table tasks add column started_at text;")
            cur.execute("alter table tasks add column completed_at text;")
            cur.execute(
                f"""
                update tasks set
                started_at = {SQLITE_TIMESTAMP("json_extract(info, '$.started_at')")},
                completed_at = {SQLITE_TIMESTAMP("json_extract(info, '$.completed_at')")},
                nid = json_extract(info, '$.nid');
            """
            )
            cur.execute("alter table data_nodes add column stale_after text;")
            cur.execute("update settings set value = '2' where key = 'version';")
            conn.commit()

        elif version == "0":
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

        else:
            raise Exception(f"Version {version} in orchestrator db.")

    def _connect(self):
        db_filename = self.data_stack.directory / "orchestrator.sqlite3"
        db_filename = db_filename.resolve()
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
            node.orchestrator = self
            self.data_nodes[node.id] = node
        return self.data_nodes

    def post_load_backpatch(self):
        for n in list(self.data_nodes.values()):
            n.backpatch_upstream()

    def check_tasks(self):
        # TODO need to go and look for tasks whose pid is in the db but they don't exist, these are zombies and should be killed 20210408:mb
        return

    def load_node_state(self, node):
        conn = self.connect()
        res = conn.execute("SELECT state FROM data_nodes WHERE nid = ?", [node.id])
        row = res.fetchone()
        if row is not None:
            node.state = DataNodeState(row[0])
            node.orchestrator = self
            return node
        else:
            return OrphanDataNode(node.id)

    def load_node_states(self):
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
        now = arrow.utcnow()
        ts = now.isoformat() + "Z"
        log_dir = self.data_stack.directory / "logs" / f"{ts}-{uuid.uuid4()}"
        fork_and_check_for_zombies(self, log_dir)
        for node in self.data_nodes.values():
            if node.state == DataNodeState.STALE:
                if node.upstream is None:
                    raise Exception(f"no upstream list for {node.id}")

                fresh = [node.is_fresh() for node in node.upstream_nodes()]

                if all(fresh):
                    fork_and_refresh(self, node, log_dir)
            else:
                refresh_at = node.next_refresh_at()
                if refresh_at is not None and refresh_at < arrow.get():
                    self.set_node_stale(node.id)

        return dict(log_dir=log_dir)

    def delete_node(self, node_id):
        node = self.data_nodes[node_id]
        info = node.info()

        with self.cursor() as cur:
            cur.execute("delete from data_nodes where nid = ?", [node_id])

        return info

    def refresh_node(self, node_id, info=None, force=True):
        if info is None:
            info = {}
        node = self.data_nodes[node_id]
        tid = trigger_refresh(self, node, info, force=force)
        return (node, self.load_task(tid))

    def set_node_stale(self, node_id):
        node = self.data_nodes[node_id]
        downstream = [node] + node.downstream_nodes()
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

    def last_task_for_node(self, nid):
        with self.cursor() as cur:
            res = cur.execute(
                """with s as (select max(started_at) as started_at from tasks where nid = ? group by nid)
                   select tid, state, nid, started_at, completed_at, info
                   from tasks
                   where started_at in (select started_at from s) and nid = ? """,
                [nid, nid],
            )
            row = res.fetchone()
            if row is None:
                return None
            else:
                return self._task_from_row(row)

    def _task_from_row(self, row):
        (tid, state, nid, started_at, completed_at, info_json) = row
        return Task(
            nid=nid,
            id=tid,
            state=state,
            started_at=started_at,
            completed_at=completed_at,
            _info=json.loads(info_json),
        )

    def load_task(self, tid):
        with self.cursor() as cur:
            res = cur.execute(
                "select tid, state, nid, started_at, completed_at, info from tasks where tid = ?",
                [tid],
            )
            return self._task_from_row(res.fetchone())

    def tasks(self):
        with self.cursor() as cur:
            res = cur.execute(
                "select tid, state, nid, started_at, completed_at, info from tasks"
            )
            return [self._task_from_row(row) for row in res.fetchall()]

    def info(self):
        nodes = self.data_nodes.values()
        tasks = self.tasks()
        return dict(
            nodes=[node.info() for node in nodes],
            tasks=[task.info() for task in tasks],
        )


@dataclass
class DataNode:
    id: str
    container: Optional[str] = None
    upstream: Optional[Sequence[Union[str, "DataNode"]]] = None
    details: Optional[dict] = None
    stale_after: Optional[str] = None
    state: Optional[DataNodeState] = None
    refresher: Optional[Callable] = None
    orchestrator: Optional[DataOrchestrator] = None

    def backpatch_upstream(self):
        nodes = self.orchestrator.data_nodes

        if isinstance(self.upstream, (str, DataNode)):
            self.upstream = [self.upstream]

        upstream = []
        for u in self.upstream:
            if isinstance(u, str):
                if u not in nodes:
                    nodes[u] = OrphanDataNode(id=u)
                upstream.append(nodes[u])
            else:
                upstream.append(u)
        self.upstream = upstream

    def upstream_nodes(self):
        if self.upstream is None:
            raise Exception(f"upstream of {self.id} is None, didn't we call backpatch?")
        return self.upstream

    def downstream_nodes(self):
        nodes = self.orchestrator.data_nodes
        downstream = {}
        for down in nodes.values():
            if self in down.upstream_nodes():
                downstream[down.id] = down

                for other in down.downstream_nodes():
                    downstream[other.id] = other

        return list(downstream.values())

    def info(self):
        i = {
            "id": self.id,
            "state": self.state.value,
            "upstream": [node.id for node in self.upstream_nodes()],
        }
        if self.container is not None:
            i["container"] = self.container
        if self.details:
            i["details"] = self.details

        last_task = self.last_task()
        if last_task is not None:
            i["last_task"] = {
                "id": last_task.id,
                "state": last_task.state,
                "started_at": last_task.started_at,
                "completed_at": last_task.completed_at,
            }
        else:
            i["last_task"] = None

        i["stale_after"] = self.stale_after
        i["next_refresh_at"] = self.next_refresh_at()

        return i

    def refresh(self, orchestrator):
        self.refresher(orchestrator)

    def is_fresh(self):
        return self.state == DataNodeState.FRESH

    def next_refresh_at(self):
        if self.orchestrator is None:
            raise ValueError(f"orchestrator for {self} is None.")
        if self.stale_after is None:
            return None
        else:
            last_task = self.orchestrator.last_task_for_node(self.id)
            if last_task is None:
                return arrow.get()
            else:
                stale_after = parse_timedelta(self.stale_after)
                stale_after_seconds = 86400 * stale_after.days + stale_after.seconds
                return arrow.get(last_task.started_at).shift(
                    seconds=stale_after_seconds
                )

    def last_task(self):
        if self.orchestrator is None:
            raise ValueError(f"orchestrator for {self} is None.")
        return self.orchestrator.last_task_for_node(self.id)


class NoopDataNode(DataNode):
    def refresh(self, orchestrator):
        return None

    def last_task(self):
        return None


class OrphanDataNode(DataNode):
    def __init__(self, id):
        super().__init__(id=id, state=DataNodeState.ORPHAN, upstream=[])

    def refresh(self, orchestrator):
        print(f"Not refreshing orphan node {self.id}.")

    def last_task(self):
        return None

    def next_refresh_at(self):
        return None


@dataclass
class Task:
    id: str
    state: str
    nid: str
    started_at: str
    completed_at: str
    _info: object

    def info(self):
        i = dict(
            id=self.id,
            state=self.state,
            nid=self.nid,
            started_at=self.started_at,
            completed_at=self.completed_at,
            info=self._info.copy(),
        )
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
    def __init__(self, state):
        super().__init__()
        self.state = state


def SQLITE_TIMESTAMP(value=None):
    if value is None:
        value = "'now'"
    return f"strftime('%Y-%m-%dT%H:%M:%f', {value})"


def _state_to_running(orchestrator, nid, tid, info):
    with orchestrator.cursor() as cur:
        cur.execute(
            f"insert into tasks (started_at, nid, tid, state, info) values ({SQLITE_TIMESTAMP()}, ?, ?, 'RUNNING', ?)",
            [
                nid,
                tid,
                json.dumps(info),
            ],
        )
        cur.execute(
            "update data_nodes set state = ?, current_tid = ? where nid = ?",
            [DataNodeState.REFRESHING.value, tid, nid],
        )


def _state_to_refreshing(orchestrator, nid, tid, info):
    with orchestrator.cursor() as cur:
        state = _fetch_one_value(
            cur, "select state from data_nodes where nid = ?", [nid]
        )
    if state == "STALE":
        _state_to_running(orchestrator, nid, tid, info)
    else:
        raise IsNotStale(state)


def _task_complete(orchestrator, nid, tid):
    with orchestrator.cursor() as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ? and current_tid = ?",
            [DataNodeState.FRESH.value, nid, tid],
        )
        cur.execute(
            f"update tasks set state = 'DONE', completed_at = {SQLITE_TIMESTAMP()} where tid = ?",
            [tid],
        )


def _task_failed(orchestrator, nid, tid, e, tb):
    with orchestrator.cursor() as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ?",
            [DataNodeState.STALE.value, nid],
        )
        info = _fetch_one_value(cur, "select info from tasks where tid = ?", [tid])
        info = json.loads(info)
        info["error"] = e
        info["traceback"] = tb
        cur.execute(
            f"update tasks set state = 'ERRORED', completed_at = {SQLITE_TIMESTAMP()}, info = ? where tid = ?",
            [json.dumps(info), tid],
        )


def trigger_refresh(orchestrator, node, info, force=False):
    print(f"Refresh on {node.id} triggered")
    pid = os.getpid()
    tid = datetime.utcnow().strftime("%Y%m%dT%H:%M:%S") + "-" + str(pid)

    info["pid"] = pid
    info["nid"] = node.id

    while True:
        try:
            _state_to_refreshing(orchestrator, node.id, tid, info)
            break
        except sqlite3.OperationalError as oe:
            print(f"sqllite3.OperationalError: {oe}")
            time.sleep(1)
        except IsNotStale as ins:
            if force:
                _state_to_running(orchestrator, node.id, tid, info)
                break
            else:
                print(f"is not stale (is {ins.state}). not refreshing.")
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

    return tid


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

    child_pid = fork()
    if child_pid > 0:
        os.waitpid(child_pid, 0)
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
            pid = info["pid"]
            if not psutil.pid_exists(pid):
                zombies += 1
                cur.execute(
                    "update tasks set state = 'ZOMBIE', completed_at = {SQLITE_TIMESTAMP()} where tid = ?",
                    [tid],
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

    child_pid = fork()
    if child_pid > 0:
        os.waitpid(child_pid, 0)
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
