class ResolutionError(Exception):
    pass


class Version:
    def __init__(self, s):
        raise NotImplementedError


class Constraint:
    @classmethod
    def parse(cls, requirement):
        raise NotImplementedError

    def allows(self, version):
        raise NotImplementedError


def resolve(roots, index):
    raise NotImplementedError
