import shlex
import os
import subprocess

join = shlex.join


def _check(subproc, arg, cwd):
    if isinstance(arg, str):
        shell = True
    else:
        shell = False
    return subproc(arg, text=True, shell=shell, cwd=cwd, bufsize=0)


def output(arg, cwd=None):
    return _check(subprocess.check_output, arg, cwd)


def call(arg, cwd=None):
    return _check(subprocess.check_call, arg, cwd)


def exec(arg):
    if isinstance(arg, str):
        args = arg.split()
    else:
        args = arg
    print(f"Calling {'|'.join(args)}")
    os.execvp(args[0], args)
