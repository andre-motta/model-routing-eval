import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX_RE = re.compile(r"(?:0|[1-9][0-9]*)")
_MISSING = object()


def _parse_pointer(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _array_index(token, length, allow_end):
    """Validate an array token; return an int index (== length means append)."""
    if token == "-":
        if allow_end:
            return length
        raise PointerError("'-' does not refer to an existing array element")
    if not _INDEX_RE.fullmatch(token):
        raise PointerError(f"invalid array index: {token!r}")
    idx = int(token)
    limit = length if allow_end else length - 1
    if idx > limit:
        raise PointerError(f"array index out of range: {token!r}")
    return idx


def _step(container, token):
    if isinstance(container, dict):
        if token not in container:
            raise PointerError(f"missing key: {token!r}")
        return container[token]
    if isinstance(container, list):
        return container[_array_index(token, len(container), False)]
    raise PointerError(f"cannot descend into scalar with token {token!r}")


def _resolve_tokens(doc, tokens):
    for token in tokens:
        doc = _step(doc, token)
    return doc


def resolve_pointer(doc, pointer):
    return _resolve_tokens(doc, _parse_pointer(pointer))


def _equal(a, b):
    """JSON equality: 1 == 1.0, but True != 1."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, dict):
        return (
            isinstance(b, dict)
            and a.keys() == b.keys()
            and all(_equal(v, b[k]) for k, v in a.items())
        )
    if isinstance(a, list):
        return (
            isinstance(b, list)
            and len(a) == len(b)
            and all(_equal(x, y) for x, y in zip(a, b))
        )
    if isinstance(b, (dict, list)):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def _add(doc, tokens, value):
    if not tokens:
        return value
    parent = _resolve_tokens(doc, tokens[:-1])
    token = tokens[-1]
    if isinstance(parent, dict):
        parent[token] = value
    elif isinstance(parent, list):
        parent.insert(_array_index(token, len(parent), True), value)
    else:
        raise PointerError("add target parent is not a container")
    return doc


def _remove(doc, tokens):
    if not tokens:
        raise PatchError("cannot remove the document root")
    parent = _resolve_tokens(doc, tokens[:-1])
    token = tokens[-1]
    if isinstance(parent, dict):
        if token not in parent:
            raise PointerError(f"missing key: {token!r}")
        return parent.pop(token)
    if isinstance(parent, list):
        return parent.pop(_array_index(token, len(parent), False))
    raise PointerError("remove target parent is not a container")


def _replace(doc, tokens, value):
    if not tokens:
        return value
    parent = _resolve_tokens(doc, tokens[:-1])
    token = tokens[-1]
    if isinstance(parent, dict):
        if token not in parent:
            raise PointerError(f"missing key: {token!r}")
        parent[token] = value
    elif isinstance(parent, list):
        parent[_array_index(token, len(parent), False)] = value
    else:
        raise PointerError("replace target parent is not a container")
    return doc


def _field(op, name, typ=None):
    if name not in op:
        raise PatchError(f"operation {op.get('op')!r} missing required field {name!r}")
    value = op[name]
    if typ is not None and not isinstance(value, typ):
        raise PatchError(f"field {name!r} must be a {typ.__name__}")
    return value


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError("operation must be an object")
    name = op.get("op")
    if not isinstance(name, str):
        raise PatchError("operation missing 'op' string")
    if name not in ("add", "remove", "replace", "move", "copy", "test"):
        raise PatchError(f"unknown op: {name!r}")
    path = _parse_pointer(_field(op, "path", str))

    if name == "add":
        return _add(doc, path, copy.deepcopy(_field(op, "value")))
    if name == "remove":
        _remove(doc, path)
        return doc
    if name == "replace":
        return _replace(doc, path, copy.deepcopy(_field(op, "value")))
    if name == "test":
        expected = _field(op, "value")
        if not _equal(_resolve_tokens(doc, path), expected):
            raise PatchError("test failed")
        return doc

    src = _parse_pointer(_field(op, "from", str))
    if name == "copy":
        return _add(doc, path, copy.deepcopy(_resolve_tokens(doc, src)))
    # move
    _resolve_tokens(doc, src)
    if len(src) < len(path) and path[: len(src)] == src:
        raise PatchError("cannot move a value into one of its own children")
    if src == path:
        return doc
    # src is non-empty here: the root is a prefix of every other path
    return _add(doc, path, _remove(doc, src))


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list of operations")
    work = copy.deepcopy(doc)
    for op in patch:
        work = _apply_op(work, op)
    if in_place:
        if isinstance(doc, dict) and isinstance(work, dict):
            doc.clear()
            doc.update(work)
            return doc
        if isinstance(doc, list) and isinstance(work, list):
            doc[:] = work
            return doc
    return work
