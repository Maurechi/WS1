#!/usr/bin/env python3
import json
import os

DIAAS_ = "DIAAS_"


def p(*things):
    for thing in things:
        print(str(thing), end="")


def removeprefix(string, prefix):
    return string[
        len(prefix) : len(string)  # noqa: E203 flake8 and black disagree here
    ]


def get_config_vars():
    config = {}
    for key, value in os.environ.items():
        if key.startswith(DIAAS_):
            config[removeprefix(key, DIAAS_)] = value
    return config


def main():
    p("window.DIAAS = ", json.dumps(get_config_vars()), ";", "\n")


if __name__ == "__main__":
    main()
