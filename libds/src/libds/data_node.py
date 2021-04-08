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
from typing import Callable, Optional, Sequence

import arrow
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
        print(f"Start refresh {self.id}.")
        self.refresher(orchestrator)
        print(f"Refresh {self.id} complete.")


class OrphanDataNode(DataNode):
    def __init__(self, id):
        super().__init__(id=id, state=DataNodeState.ORPHAN)

    def refresh(self, orchestrator):
        print(f"Not refreshing orphan node {self.id}.")


class DataOrchestrator:
    def __init__(self, data_stack):
        self.data_stack = data_stack

    def _ensure_schema(self, conn):
        res = conn.execute(
            "select count(*) from sqlite_schema where type = 'table' and tbl_name = 'settings'"
        )
        count = res.fetchone()[0]
        if count == 0:
            cur = conn.cursor()
            cur.execute("begin")
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
            cur.execute("begin")
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

    def check_tasks(self):
        # TODO need to go and look for tasks whose pid is in the db but they don't exist, these are zombies and should be killed 20210408:mb
        return

    def load_states(self):
        conn = self.connect()
        nodes = self.data_stack.data_nodes

        conn.execute("begin;")
        res = conn.execute("SELECT nid, state FROM data_nodes").fetchall()

        for id, state in res:
            if id in nodes:
                nodes[id].state = DataNodeState(state)
            else:
                nodes[id] = OrphanDataNode(id)

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
                if node.upstream is None:
                    raise Exception(f"no upstream list for {node.id}")
                if all(
                    [nodes[nid].state == DataNodeState.FRESH for nid in node.upstream]
                ):
                    fork_and_refresh(self, node, log_dir)

        return dict(log_dir=log_dir)

    def downstream_nodes(self, node):
        downstream = {}
        for down in self.data_stack.data_nodes.values():
            if node.id in down.upstream:
                downstream[down.id] = down

                for other in self.downstream_nodes(down):
                    downstream[other.id] = other

        return list(downstream.values())

    def set_node_state(self, node_id, state):
        nodes = self.data_stack.data_nodes
        node = nodes[node_id]
        if node.state == state:
            return

        if state == DataNodeState.STALE:
            downstream = [node] + self.downstream_nodes(node)
            downstream = [n.id for n in downstream]
            with cursor(self) as cur:
                cur.execute(
                    f"update data_nodes set state = 'STALE' where state = 'FRESH' and nid in ({ ','.join(['?'] * len(downstream)) })",
                    downstream,
                )
                cur.execute(
                    f"update data_nodes set state = 'REFRESHING_STALE' where state = 'REFRESHING' and nid in ({ ','.join(['?'] * len(downstream)) })",
                    downstream,
                )
        else:
            with cursor(self) as cur:
                cur.execute(
                    "update data_nodes set state = ? where nid = ?", [state, node_id]
                )

    def info(self):
        return [node.info() for node in self.data_stack.data_nodes.values()]


def fork():
    try:
        return os.fork()
    except OSError as err:
        print(f"{os.getpid()}: fork failed:", err, file=sys.stderr)
        raise err


@contextmanager
def cursor(orchestrator):
    conn = orchestrator.connect()
    cur = conn.cursor()
    cur.execute("begin;")

    yield cur

    conn.commit()
    conn.close()


class IsNotStale(Exception):
    pass


def _state_to_refreshing(orchestrator, nid, tid):
    with cursor(orchestrator) as cur:
        state = cur.execute("select state from data_nodes where nid = ?", [nid])
        state = state.fetchone()[0]
        if state == "STALE":
            tid = str(os.getpid())
            cur.execute("insert into tasks (tid, state) values (?, '{}')", [tid])
            cur.execute(
                "update data_nodes set state = ?, current_tid = ? where nid = ?",
                [DataNodeState.REFRESHING.value, tid, nid],
            )
        else:
            raise IsNotStale()


def _state_to_fresh(orchestrator, nid, tid):
    with cursor(orchestrator) as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ? and current_tid = ?",
            [DataNodeState.FRESH.value, nid, tid],
        )
        cur.execute("delete from tasks where tid = ?", [tid])


def _state_to_stale(orchestrator, nid, tid):
    with cursor(orchestrator) as cur:
        cur.execute(
            "update data_nodes set state = ?, current_tid = null where nid = ?",
            [DataNodeState.STALE.value, nid],
        )
        cur.execute("delete from tasks where tid = ?", [tid])


def trigger_refresh(orchestrator, node):
    print(f"Refresh on {node.id} triggered")
    tid = str(os.getpid())

    while True:
        try:
            _state_to_refreshing(orchestrator, node.id, tid)
            print(f"{node.id} is stale")
            break
        except sqlite3.OperationalError:
            pass
        except IsNotStale:
            print(f"{node.id} is not stale. not refreshing.")
            return

    try:
        node.refresh(orchestrator)
        print(f"{node.id} refresh complete")
        while True:
            try:
                _state_to_fresh(orchestrator, node.id, tid)
                print(f"{node.id} set to fresh")
                break
            except sqlite3.OperationalError:
                pass
    except Exception as e:
        print(f"{node.id} refresh error, setting back to stale")
        while True:
            try:
                _state_to_stale(orchestrator, node.id, tid)
                print(f"{node.id} set to stale")
                break
            except sqlite3.OperationalError:
                pass
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


def fork_and_refresh(orchestrator, node, log_dir):
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

    setproctitle.setproctitle(sys.argv[0] + " data-node-refresh " + node.id)

    sys.stdout = TaskOutputStream(stdout_file)
    sys.stderr = TaskOutputStream(stderr_file)

    with pid_file.open("w") as file:
        print(str(os.getpid()), file=file)

    trigger_refresh(orchestrator, node)

    if pid_file.exists():
        pid_file.unlink()

    sys.exit(0)
