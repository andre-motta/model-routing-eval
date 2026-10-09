import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX = re.compile(r"0|[1-9][0-9]*")

_OPS = ("add", "remove", "replace", "move", "copy", "test")


def _tokens(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _index(token, pointer):
    if not _INDEX.fullmatch(token):
        raise PointerError(f"invalid array index {token!r} in {pointer!r}")
    return int(token)


def _child(container, token, pointer):
    if isinstance(container, dict):
        if token not in container:
            raise PointerError(f"key {token!r} not found in {pointer!r}")
        return container[token]
    if isinstance(container, list):
        idx = _index(token, pointer)
        if idx >= len(container):
            raise PointerError(f"index {idx} out of range in {pointer!r}")
        return container[idx]
    raise PointerError(f"cannot descend into scalar at {token!r} in {pointer!r}")


def resolve_pointer(doc, pointer):
    node = doc
    for token in _tokens(pointer):
        node = _child(node, token, pointer)
    return node


def _parent(doc, pointer):
    tokens = _tokens(pointer)
    if not tokens:
        raise PatchError("operation needs a non-root path")
    node = doc
    for token in tokens[:-1]:
        node = _child(node, token, pointer)
    return node, tokens[-1]


def _add(doc, pointer, value):
    if not _tokens(pointer):
        return copy.deepcopy(value)
    parent, last = _parent(doc, pointer)
    if isinstance(parent, dict):
        parent[last] = copy.deepcopy(value)
    elif isinstance(parent, list):
        if last == "-":
            parent.append(copy.deepcopy(value))
        else:
            idx = _index(last, pointer)
            if idx > len(parent):
                raise PointerError(f"index {idx} out of range in {pointer!r}")
            parent.insert(idx, copy.deepcopy(value))
    else:
        raise PointerError(f"cannot add into scalar at {pointer!r}")
    return doc


def _remove(doc, pointer):
    if not _tokens(pointer):
        raise PatchError("cannot remove the document root")
    parent, last = _parent(doc, pointer)
    if isinstance(parent, dict):
        if last not in parent:
            raise PointerError(f"key {last!r} not found in {pointer!r}")
        del parent[last]
    elif isinstance(parent, list):
        idx = _index(last, pointer)
        if idx >= len(parent):
            raise PointerError(f"index {idx} out of range in {pointer!r}")
        del parent[idx]
    else:
        raise PointerError(f"cannot remove from scalar at {pointer!r}")
    return doc


def _replace(doc, pointer, value):
    if not _tokens(pointer):
        return copy.deepcopy(value)
    parent, last = _parent(doc, pointer)
    if isinstance(parent, dict):
        if last not in parent:
            raise PointerError(f"key {last!r} not found in {pointer!r}")
        parent[last] = copy.deepcopy(value)
    elif isinstance(parent, list):
        idx = _index(last, pointer)
        if idx >= len(parent):
            raise PointerError(f"index {idx} out of range in {pointer!r}")
        parent[idx] = copy.deepcopy(value)
    else:
        raise PointerError(f"cannot replace inside scalar at {pointer!r}")
    return doc


def _equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError(f"operation must be an object, got {type(op).__name__}")
    name = op.get("op")
    if name not in _OPS:
        raise PatchError(f"unknown op {name!r}")
    path = op.get("path")
    if not isinstance(path, str):
        raise PatchError(f"{name} requires a string 'path'")

    if name in ("add", "replace", "test") and "value" not in op:
        raise PatchError(f"{name} requires 'value'")
    if name in ("move", "copy"):
        source = op.get("from")
        if not isinstance(source, str):
            raise PatchError(f"{name} requires a string 'from'")

    if name == "add":
        return _add(doc, path, op["value"])
    if name == "remove":
        return _remove(doc, path)
    if name == "replace":
        return _replace(doc, path, op["value"])
    if name == "copy":
        value = copy.deepcopy(resolve_pointer(doc, source))
        return _add(doc, path, value)
    if name == "move":
        src_tokens = _tokens(source)
        dst_tokens = _tokens(path)
        if len(dst_tokens) > len(src_tokens) and dst_tokens[:len(src_tokens)] == src_tokens:
            raise PatchError(f"cannot move {source!r} into its own child {path!r}")
        value = resolve_pointer(doc, source)
        if src_tokens == dst_tokens:
            return doc
        doc = _remove(doc, source)
        return _add(doc, path, value)
    # test
    actual = resolve_pointer(doc, path)
    if not _equal(actual, op["value"]):
        raise PatchError(f"test failed at {path!r}")
    return doc


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError(f"patch must be a list, got {type(patch).__name__}")

    # Work on a copy so a failure part way through leaves the input untouched.
    result = copy.deepcopy(doc)
    for op in patch:
        result = _apply_op(result, op)

    if in_place and isinstance(doc, dict) and isinstance(result, dict):
        doc.clear()
        doc.update(result)
        return doc
    if in_place and isinstance(doc, list) and isinstance(result, list):
        doc[:] = result
        return doc
    return result
