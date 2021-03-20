import hashlib
import secrets
import threading


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


class Progress:
    def __init__(self, progress=None):
        self.c = 0
        self.step = 1
        self.progress = progress
        self.last_value = None

    def tick(self, value):
        self.last_value = value
        self.c += 1
        if self.c % self.step == 0:
            self.progress(self.c, self.last_value)
        if self.c >= 10 * self.step:
            self.step = self.step * 10
        return value