import sys
import shlex
import os
import subprocess

join = shlex.join


def _check(subproc, cmd, cwd):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    sys.stdout.flush()
    sys.stderr.flush()
    return subproc(cmd, text=True, shell=shell, cwd=cwd, bufsize=0)


def output(cmd, cwd=None):
    return _check(subprocess.check_output, cmd, cwd)


def call(cmd, cwd=None):
    return _check(subprocess.check_call, cmd, cwd)


def exec(cmd, cwd=None):
    if isinstance(cmd, str):
        args = cmd.split()
    else:
        args = cmd
    sys.stdout.flush()
    sys.stderr.flush()
    os.chdir(cwd)
    os.execvp(args[0], args)


class EnvironDict:
    def __getattr__(self, name):
        return os.environ[name]

    def __setattr__(self, name, value):
        os.environ[name] = value
        return value


env = EnvironDict()
