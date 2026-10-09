import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX_RE = re.compile(r"0|[1-9][0-9]*")
_OPS = ("add", "remove", "replace", "move", "copy", "test")
_NEEDS_VALUE = ("add", "replace", "test")
_NEEDS_FROM = ("move", "copy")


def _tokens(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _child(container, token, pointer):
    if isinstance(container, dict):
        if token not in container:
            raise PointerError(f"key {token!r} not found for pointer {pointer!r}")
        return container[token]
    if isinstance(container, list):
        if not _INDEX_RE.fullmatch(token):
            raise PointerError(f"invalid array index {token!r} for pointer {pointer!r}")
        index = int(token)
        if index >= len(container):
            raise PointerError(f"index {index} out of range for pointer {pointer!r}")
        return container[index]
    raise PointerError(f"cannot traverse into scalar for pointer {pointer!r}")


def _parent(doc, pointer):
    tokens = _tokens(pointer)
    if not tokens:
        raise PointerError("the document root has no parent")
    parent = doc
    for token in tokens[:-1]:
        parent = _child(parent, token, pointer)
    return parent, tokens[-1]


def _set(parent, key, value, pointer):
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        parent[int(key)] = value
    else:
        raise PointerError(f"cannot set into scalar for pointer {pointer!r}")


def _json_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def resolve_pointer(doc, pointer):
    node = doc
    for token in _tokens(pointer):
        node = _child(node, token, pointer)
    return node


def _add(doc, pointer, value):
    if not _tokens(pointer):
        return value
    parent, key = _parent(doc, pointer)
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        if key == "-":
            parent.append(value)
        elif _INDEX_RE.fullmatch(key) and int(key) <= len(parent):
            parent.insert(int(key), value)
        else:
            raise PointerError(f"invalid insert index {key!r} for pointer {pointer!r}")
    else:
        raise PointerError(f"cannot add into scalar for pointer {pointer!r}")
    return doc


def _remove(doc, pointer):
    if not _tokens(pointer):
        raise PatchError("cannot remove the document root")
    parent, key = _parent(doc, pointer)
    _child(parent, key, pointer)
    if isinstance(parent, dict):
        del parent[key]
    else:
        del parent[int(key)]
    return doc


def _replace(doc, pointer, value):
    if not _tokens(pointer):
        return value
    parent, key = _parent(doc, pointer)
    _child(parent, key, pointer)
    _set(parent, key, value, pointer)
    return doc


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError("each operation must be an object")
    name = op.get("op")
    if name not in _OPS:
        raise PatchError(f"unknown op: {name!r}")
    path = op.get("path")
    if not isinstance(path, str):
        raise PatchError(f"{name}: 'path' must be a string")
    if name in _NEEDS_VALUE and "value" not in op:
        raise PatchError(f"{name}: missing 'value'")
    if name in _NEEDS_FROM and not isinstance(op.get("from"), str):
        raise PatchError(f"{name}: 'from' must be a string")

    if name == "add":
        return _add(doc, path, copy.deepcopy(op["value"]))
    if name == "remove":
        return _remove(doc, path)
    if name == "replace":
        return _replace(doc, path, copy.deepcopy(op["value"]))
    if name == "move":
        source = op["from"]
        if path.startswith(source + "/"):
            raise PatchError("move: 'from' must not be a proper prefix of 'path'")
        value = resolve_pointer(doc, source)
        doc = _remove(doc, source)
        return _add(doc, path, value)
    if name == "copy":
        value = copy.deepcopy(resolve_pointer(doc, op["from"]))
        return _add(doc, path, value)
    if not _json_equal(resolve_pointer(doc, path), op["value"]):
        raise PatchError(f"test failed at {path!r}")
    return doc


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list of operations")
    result = copy.deepcopy(doc)
    for op in patch:
        result = _apply_op(result, op)
    if not in_place:
        return result
    if isinstance(doc, dict) and isinstance(result, dict):
        doc.clear()
        doc.update(result)
        return doc
    if isinstance(doc, list) and isinstance(result, list):
        doc[:] = result
        return doc
    return result
