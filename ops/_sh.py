import shlex
import os
import subprocess

join = shlex.join


def output(arg):
    if isinstance(arg, str):
        shell = True
    else:
        shell = False
    return subprocess.check_output(arg, text=True, shell=shell).rstrip()


def call(arg):
    if isinstance(arg, str):
        shell = True
    else:
        shell = False
    return subprocess.check_call(arg, text=True, shell=shell)


def exec(arg):
    if isinstance(arg, str):
        args = arg.split()
    else:
        args = arg
    print(f"Calling {'|'.join(args)}")
    os.execvp(args[0], args)
