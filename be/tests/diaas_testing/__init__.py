from pprint import pformat


class ExpectationFailure(Exception):
    pass


class Expect:
    def __init__(self, value):
        self.value = value
        self.msg = None

    @property
    def to(self):
        return self

    def _contains(self, value, other, path=""):
        for key in other.keys():
            if key not in value:
                self.msg = [f"Missing {path}.{key} in"] + pformat(value).split("\n")
                return False
            v = value[key]
            if isinstance(v, dict):
                return self._contains(v, other[key], path=path + "." + key)
        return True

    def __ge__(self, other):
        return self._contains(self.value, other)

    def contain(self, other):
        return self._contains(self.value, other)


expect = Expect
