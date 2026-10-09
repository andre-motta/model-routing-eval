class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


def resolve_pointer(doc, pointer):
    raise NotImplementedError


def apply_patch(doc, patch, in_place=False):
    raise NotImplementedError
