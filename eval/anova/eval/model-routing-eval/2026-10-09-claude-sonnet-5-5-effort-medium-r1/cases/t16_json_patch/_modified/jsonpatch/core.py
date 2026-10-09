import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX_RE = re.compile(r"(0|[1-9][0-9]*)\Z")
_OPS = ("add", "remove", "replace", "move", "copy", "test")


def _parse_pointer(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _index(token, container_len, allow_end=False):
    """Convert an array token to an int index, validating range."""
    if allow_end and token == "-":
        return container_len
    if not _INDEX_RE.match(token):
        raise PointerError(f"invalid array index: {token!r}")
    idx = int(token)
    limit = container_len if allow_end else container_len - 1
    if idx > limit:
        raise PointerError(f"array index out of range: {token!r}")
    return idx


def _step(node, token):
    if isinstance(node, dict):
        if token not in node:
            raise PointerError(f"key not found: {token!r}")
        return node[token]
    if isinstance(node, list):
        return node[_index(token, len(node))]
    raise PointerError(f"cannot descend into {type(node).__name__} with {token!r}")


def _walk(doc, tokens):
    node = doc
    for token in tokens:
        node = _step(node, token)
    return node


def resolve_pointer(doc, pointer):
    return _walk(doc, _parse_pointer(pointer))


def _equal(a, b):
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
    if isinstance(a, (int, float)):
        return isinstance(b, (int, float)) and a == b
    return type(a) is type(b) and a == b


def _add(doc, tokens, value):
    """Return the document with value added at tokens (may mutate doc)."""
    if not tokens:
        return value
    parent = _walk(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, dict):
        parent[last] = value
    elif isinstance(parent, list):
        parent.insert(_index(last, len(parent), allow_end=True), value)
    else:
        raise PointerError(f"cannot add into {type(parent).__name__}")
    return doc


def _remove(doc, tokens):
    """Remove the value at tokens, returning (doc, removed)."""
    if not tokens:
        raise PatchError("cannot remove the document root")
    parent = _walk(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, dict):
        if last not in parent:
            raise PointerError(f"key not found: {last!r}")
        return doc, parent.pop(last)
    if isinstance(parent, list):
        return doc, parent.pop(_index(last, len(parent)))
    raise PointerError(f"cannot remove from {type(parent).__name__}")


def _replace(doc, tokens, value):
    if not tokens:
        return value
    parent = _walk(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, dict):
        if last not in parent:
            raise PointerError(f"key not found: {last!r}")
        parent[last] = value
    elif isinstance(parent, list):
        parent[_index(last, len(parent))] = value
    else:
        raise PointerError(f"cannot replace in {type(parent).__name__}")
    return doc


def _require(op, field):
    if field not in op:
        raise PatchError(f"operation {op.get('op')!r} missing required field {field!r}")
    return op[field]


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError(f"operation must be an object, got {type(op).__name__}")
    name = op.get("op")
    if not isinstance(name, str) or name not in _OPS:
        raise PatchError(f"unknown op: {name!r}")
    path = _parse_pointer(_require(op, "path"))

    if name == "add":
        return _add(doc, path, copy.deepcopy(_require(op, "value")))
    if name == "remove":
        return _remove(doc, path)[0]
    if name == "replace":
        _walk(doc, path)
        return _replace(doc, path, copy.deepcopy(_require(op, "value")))
    if name == "test":
        if not _equal(_walk(doc, path), _require(op, "value")):
            raise PatchError(f"test failed at {op['path']!r}")
        return doc

    src = _parse_pointer(_require(op, "from"))
    if name == "copy":
        return _add(doc, path, copy.deepcopy(_walk(doc, src)))
    # move
    _walk(doc, src)
    if len(src) < len(path) and path[: len(src)] == src:
        raise PatchError("cannot move a value into one of its own children")
    if src == path:
        return doc
    doc, value = _remove(doc, src)
    return _add(doc, path, value)


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
