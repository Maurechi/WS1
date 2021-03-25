import multiprocessing as mp
import time
import traceback
from pprint import pformat, pprint  # noqa: F401


def apply_task(task):
    # print("_apply_task({pformat(task)})")
    # return task.execute()
    return None


def orchestrator(o):
    try:
        with mp.Pool(processes=2, maxtasksperchild=1) as pool:
            while True:
                o.tick(pool)
                if o.done:
                    break
                else:
                    time.sleep(1)
    except Exception as e:
        o.queue.put([True, traceback.format_exc()])
        raise e
    o.queue.put([False, None])


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

        self.tasks = [TaskState(task) for task in tasks]

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
                print(f"{t.task.id}: INIT")
                t.state = "PENDING"
                t.result = None
                t.async_result = None
                t.blockers = [
                    self.task_with_id(task.task.id, task)
                    for task in self.make_task_states(t.task.pre_requisites())
                ]
                self.tasks = self.add_tasks(self.tasks, t.blockers)
            elif t.state == "PENDING":
                print(f"{t.task.id}: PENDING")
                t.blockers = [task for task in t.blockers if task.state != "DONE"]
                if len(t.blockers) == 0:
                    print("  No blockers, running")
                    t.async_result = pool.apply_async(apply_task, args=[t.task])
                    t.state = "RUNNING"
                else:
                    print(f"  {len(t.blockers)} blockers:")
                    for b in t.blockers:
                        print(f"    {b.task.id} {b.state}")
            elif t.state == "RUNNING":
                print(f"{t.task.id}: RUNNING")
                try:
                    res = t.async_result.get(0)
                    print("  COMPLETE")
                    t.state = "DONE"
                    t.result = res
                    for t2 in self.tasks:
                        t2.blockers = self.discard_tasks(t2.blockers, [t])
                    self.tasks = self.add_tasks(
                        self.tasks, self.make_task_states(t.task.post_requisites())
                    )
                except mp.TimeoutError:
                    print("  IN PROGRESS")

        done = True
        print("States: " + ",".join([str(t.state) for t in self.tasks]))
        for t in self.tasks:
            if t.state != "DONE":
                done = False
        self.done = done

        return self

    def execute(self):
        self.process = mp.Process(target=orchestrator, args=[self])
        self.process.start()
        return self

    def wait(self):
        err, msg = self.queue.get()
        if err:
            raise Exception(f"Exception in orchestrator thread: {msg}")
        else:
            return self


class Task:
    def __init__(self, id):
        self.id = id

    def pre_requisites(self):
        return []

    def post_requisites(self):
        return []

    def execute(self):
        print(f"{self.id} executing.")
        return True
