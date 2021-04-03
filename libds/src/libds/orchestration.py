import multiprocessing as mp
import os
import re
import sys
import time
import traceback
import uuid
from pathlib import Path
from pprint import pformat, pprint  # noqa: F401

import arrow


def apply_task(task, log_dir):
    sys.stdout = (log_dir / f"{task.id}.stdout").open("w")
    sys.stderr = (log_dir / f"{task.id}.stderr").open("w")
    return task.execute()


def dbg(*msg, file=None):
    if file is None:
        file = sys.stdout

    prefix = f"{os.getpid()}@{arrow.get()}"
    text = [prefix]
    msg = list(msg)

    for o in msg:
        if not re.match(r"\s+$", text[-1]):
            text.append(" ")

        if isinstance(o, (str, int)):
            text.append(str(o))
        else:
            text.append(pformat(o))

    line = "".join(text)
    print(line, file=file)
    return line


class TaskState:
    def __init__(self, task):
        self.task = task
        self.state = None


class Orchestrator:
    def __init__(self, tasks):
        self.done = False
        self.concurrency = 2
        self.process = None
        self.queue = mp.Queue()

        self.tasks = []
        for task in tasks:
            if task.id not in [t.task.id for t in self.tasks]:
                self.tasks.append(TaskState(task))

    def add_tasks(self, list, tasks):
        for task in tasks:
            if task.task.id not in [t.task.id for t in list]:
                list = list + [task]
        return list

    def discard_tasks(self, list, tasks):
        for task in tasks:
            list = [t for t in list if t.task.id != task.task.id]
        return list

    def make_task_states(self, tasks):
        return [TaskState(task) for task in tasks]

    def task_with_id(self, id, otherwise):
        for t in self.tasks:
            if t.task.id == id:
                return t
        else:
            return otherwise

    def tick(self, pool):
        tasks = self.tasks
        for t in tasks:
            if t.state is None:
                dbg(t.task.id, "INIT")
                t.state = "PENDING"
                t.result = None
                t.async_result = None
                t.blockers = [
                    self.task_with_id(task.task.id, task)
                    for task in self.make_task_states(t.task.pre_requisites())
                ]
                self.tasks = self.add_tasks(self.tasks, t.blockers)
            elif t.state == "PENDING":
                dbg(t.task.id, "PENDING")
                t.blockers = [task for task in t.blockers if task.state != "DONE"]
                if len(t.blockers) == 0:
                    dbg("  No blockers, running")
                    t.async_result = pool.apply_async(
                        apply_task, args=[t.task, self.log_dir]
                    )
                    t.state = "RUNNING"
                else:
                    dbg("  ", len(t.blockers), "blockers:")
                    for b in t.blockers:
                        dbg("    ", b.task.id, b.state)
            elif t.state == "RUNNING":
                dbg(t.task.id, "RUNNING")
                try:
                    res = t.async_result.get(0)
                    dbg("  COMPLETE")
                    t.state = "DONE"
                    t.result = res
                    for t2 in self.tasks:
                        t2.blockers = self.discard_tasks(t2.blockers, [t])
                    self.tasks = self.add_tasks(
                        self.tasks, self.make_task_states(t.task.post_requisites())
                    )
                except mp.TimeoutError:
                    dbg("  IN PROGRESS")

        done = True
        dbg("States:", [str(t.state) for t in self.tasks])
        for t in self.tasks:
            if t.state != "DONE":
                done = False
        self.done = done

        return self

    def fork(self):
        try:
            return os.fork()
        except OSError as err:
            dbg("fork failed:", err, file=sys.stderr)
            sys.exit(1)

    def orchestrate_inner(self):
        try:
            with mp.Pool(processes=2, maxtasksperchild=1) as pool:
                while True:
                    self.tick(pool)
                    if self.done:
                        break
                    else:
                        time.sleep(1)
        except Exception:
            tb = traceback.format_exc()
            dbg("Done with error:", tb)
            return [True, tb]
        dbg("Done without errors")
        return [False, None]

    def orchestrate(self):
        stdout = sys.stdout
        stderr = sys.stderr

        with self.pid_file.open("w") as f:
            print(str(os.getpid()), file=f)

        sys.stdout = (self.log_dir / "orchestrator.stdout").open("w")
        sys.stderr = (self.log_dir / "orchestrator.stderr").open("w")
        ret = self.orchestrate_inner()
        sys.stdout = stdout
        sys.stderr = stderr

        if self.pid_file.exists():
            self.pid_file.unlink()

        return ret

    def execute(self, wait=False):
        self.id = f"{arrow.get()}-{uuid.uuid4()}"
        self.log_dir = Path("logs") / self.id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.log_dir / "pid.txt"

        if wait:
            err, msg = self.orchestrate()
            if err:
                raise Exception(f"Exception in orchestrator thread: {msg}")
            else:
                return None
        else:
            if self.fork() > 0:
                return self.pid_file

            # NOTE From this point on we're in the child and we never return 20210326:mb

            os.setsid()
            os.umask(0)

            if self.fork() > 0:
                sys.exit()

            self.orchestrate()

            sys.exit(0)


class Task:
    def __init__(self, id):
        self.id = id

    def pre_requisites(self):
        return []

    def post_requisites(self):
        return []

    def execute(self):
        raise NotImplementedError()


class Job:
    def __init__(self, dir):
        self.directory = dir

    def info(self):
        data = {"id": self.directory.name}
        try:
            pid_string = (self.directory / "pid.txt").open("r").read().strip()
            data["state"] = "RUNNING"
            data["pid"] = int(pid_string)
        except FileNotFoundError:
            data["state"] = "DONE"

        data["orchestrator"] = {}
        try:
            data["orchestrator"]["stdout"] = (
                (self.directory / "orchestrator.stdout").open("r").read()
            )
        except FileNotFoundError:
            pass
        try:
            data["orchestrator"]["stderr"] = (
                (self.directory / "orchestrator.stderr").open("r").read()
            )
        except FileNotFoundError:
            pass

        return data


def load_jobs(data_stack):
    jobs = []
    for dirname in (data_stack.directory / "logs").glob("*"):
        if dirname in (".", ".."):
            continue
        dir = Path(dirname)
        if dir.is_dir():
            jobs.append(Job(dir))
    return jobs
