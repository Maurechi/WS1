# NOTE This file is tech debt. Getting something up and running is the
# primary goal for now, but we're rebuilding singer and sqlalchemy and
# this is not a long term solution. 20210429:mb
from dataclasses import dataclass


@dataclass
class DataType:
    is_nullable: bool = False


@dataclass
class Integer(DataType):
    width: int = None


@dataclass
class Decimal(DataType):
    precision: int = None
    scale: int = None


@dataclass
class Float(DataType):
    width: int = None


@dataclass
class Text(DataType):
    length: int = None
