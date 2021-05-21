import hashlib
import io
import secrets
import threading
import time
from collections import defaultdict
from pathlib import Path

from ruamel.yaml import YAML


class ThreadLocalList(threading.local):
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = []

    def extend(self, elements):
        self.value.extend(elements)

    def append(self, *elements):
        self.extend(elements)

    def __iter__(self):
        return self.value.__iter__()

    def __len__(self):
        return len(self.value)

    def __getitem__(self, key):
        return self.value[key]


class ThreadLocalValue(threading.local):
    def __init__(self):
        self.value = None


def hash_password(pw):
    salt = secrets.token_bytes(16)
    # https://cryptobook.nakov.com/mac-and-key-derivation/scrypt
    hash = hashlib.scrypt(
        password=pw.encode("utf-8"), salt=salt, dklen=20, n=16384, r=8, p=1
    )
    return f"scrypt${salt.hex()}${hash.hex()}"


class InsertProgress:
    def __init__(self, make_message=None):
        self.c = 0
        self.step = 1
        self.make_message = make_message
        self.last_values = None
        self.last_display_at = None
        self.interval = 30

    def update(self, values):
        self.last_values = values
        self.c += 1
        if (self.c % self.step == 0) or (
            self.last_display_at < (time.time() - self.interval)
        ):
            self.display()

        if self.c >= 10 * self.step:
            self.step = self.step * 10

        return values

    def display(self, message=None):
        if message is None:
            message = self.make_message(self.c, self.last_values)
        print(message, flush=True)
        self.last_display_at = time.time()


class GaugeProgress:
    def __init__(self, make_message=None):
        self.make_message = make_message
        self.last_display_at = None
        self.interval = 1

    def update(self, values):
        self.last_values = values
        now = time.time()
        if self.last_display_at is None:
            self.display()

        elif self.last_display_at < (now - self.interval):
            self.display()
            self.interval = min(120, self.interval * 1.2)

    def display(self, message=None):
        if message is None:
            message = self.make_message(self.last_values)
        print(message, flush=True)
        self.last_display_at = time.time()


class DependencyGraph:
    def __init__(self):
        self.edges = defaultdict(list)
        self.nodes = set()

    def edge(self, src, dst):
        self.nodes.add(src)
        self.nodes.add(dst)
        self.edges[src].append(dst)

    def cascade_from_node(self, node):
        # NOTE in python3.7 and up dicts guarantee insertion order. 20210320:mb
        ordering = {}

        def walk(n):
            ordering[n] = True
            for next in self.edges[n]:
                walk(next)

        walk(node)
        return ordering.keys()

    def cascade_from_nodes(self, nodes):
        # NOTE in python3.7 and up dicts guarantee insertion order. 20210320:mb
        backwards = {}
        for ordering in [self.cascade_from_node(node) for node in nodes]:
            for node in reversed(ordering):
                backwards[node] = True
        return reversed(backwards.keys())


class DoesNotExist(Exception):
    pass


class DSException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def code(self):
        return self.__class__.__module__ + "." + self.__class__.__name__

    def as_json(self):
        return dict(code=self.code(), details=str(self))


def timedelta_as_info(td):
    info = {}
    days = td.days

    if days > 7:
        info["weeks"] = int(days / 7)
        days = days % 7

    if days > 0:
        info["days"] = days

    secs = td.seconds
    if secs > 3600:
        info["hours"] = int(secs / 3600)
        secs = secs % 3600

    if secs > 60:
        info["minutes"] = int(secs / 60)
        secs = secs % 60

    if secs > 0:
        info["seconds"] = secs

    return info


def is_iterable(thing):
    try:
        _ = (e for e in thing)
        return True
    except TypeError:
        return False


def yaml_dump(object, file):
    if isinstance(file, str):
        file = Path(str)
    if isinstance(file, Path):
        file = file.open("w")
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.indent(sequence=2, mapping=2, offset=2)
    yaml.dump(object, file)
    return object


def yaml_load(file=None, string=None):
    if string is not None:
        return YAML(typ="rt").load(io.StringIO(string))
    else:
        if isinstance(file, str):
            file = Path(str)
        if isinstance(file, Path):
            file = file.open("r")
        return YAML(typ="rt").load(file)
