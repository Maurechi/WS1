import multiprocessing as mp


class Orchestrator:
    def __init__(self, tasks):
        self.tasks = sorted(tasks, key=lambda t: t.id)

    def execute(self):
        state = {}
        for t in self.tasks:
            state[t] = 'PENDING'

        with mp.Pool(processes=2, maxtasksperchild=1) as pool:
            while True:
                seen = {}
                t0 = self.tasks[0]
                for pre in t0.pre_prerequisites():
                    if pre in seen:
                        raise Exception("Circular dependency detected")


class Task:
    def __init__(self, id):
        self.id = id

    def pre_prerequisites(self):
        return []

    def post_prerequisites(self):
        return []

    def execute(self):
        pass
