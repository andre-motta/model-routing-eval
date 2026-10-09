import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX = re.compile(r"(0|[1-9][0-9]*)\Z")


def _parse(pointer):
    if not isinstance(pointer, str):
        raise PointerError("pointer must be a string")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError("pointer must start with '/'")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _index(token, arr, allow_end):
    if token == "-" and allow_end:
        return len(arr)
    if not _INDEX.match(token):
        raise PointerError(f"invalid array index {token!r}")
    i = int(token)
    if i > len(arr) or (i == len(arr) and not allow_end):
        raise PointerError(f"array index out of range: {token}")
    return i


def _step(node, token):
    if isinstance(node, dict):
        if token not in node:
            raise PointerError(f"missing key {token!r}")
        return node[token]
    if isinstance(node, list):
        return node[_index(token, node, False)]
    raise PointerError("cannot traverse into scalar")


def resolve_pointer(doc, pointer):
    node = doc
    for token in _parse(pointer):
        node = _step(node, token)
    return node


def _parent(doc, tokens):
    node = doc
    for token in tokens[:-1]:
        node = _step(node, token)
    if not isinstance(node, (dict, list)):
        raise PointerError("parent is not a container")
    return node


def _add(doc, pointer, value):
    tokens = _parse(pointer)
    if not tokens:
        return value
    parent = _parent(doc, tokens)
    if isinstance(parent, dict):
        parent[tokens[-1]] = value
    else:
        parent.insert(_index(tokens[-1], parent, True), value)
    return doc


def _remove(doc, pointer):
    tokens = _parse(pointer)
    if not tokens:
        raise PatchError("cannot remove the document root")
    parent = _parent(doc, tokens)
    if isinstance(parent, dict):
        if tokens[-1] not in parent:
            raise PointerError(f"missing key {tokens[-1]!r}")
        return parent.pop(tokens[-1])
    return parent.pop(_index(tokens[-1], parent, False))


def _equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        return False
    return a == b


def _apply_one(doc, op):
    if not isinstance(op, dict):
        raise PatchError("operation must be an object")
    name = op.get("op")
    if name not in ("add", "remove", "replace", "move", "copy", "test"):
        raise PatchError(f"unknown op {name!r}")
    path = op.get("path")
    if not isinstance(path, str):
        raise PatchError("missing or invalid 'path'")
    if name in ("add", "replace", "test") and "value" not in op:
        raise PatchError("missing 'value'")
    if name in ("move", "copy"):
        src = op.get("from")
        if not isinstance(src, str):
            raise PatchError("missing or invalid 'from'")

    if name == "add":
        return _add(doc, path, copy.deepcopy(op["value"]))
    if name == "remove":
        _remove(doc, path)
        return doc
    if name == "replace":
        resolve_pointer(doc, path)
        if path == "":
            return copy.deepcopy(op["value"])
        _remove(doc, path)
        return _add(doc, path, copy.deepcopy(op["value"]))
    if name == "test":
        if not _equal(resolve_pointer(doc, path), op["value"]):
            raise PatchError("test failed")
        return doc
    if name == "copy":
        return _add(doc, path, copy.deepcopy(resolve_pointer(doc, src)))
    # move
    sp, dp = _parse(src), _parse(path)
    if len(sp) < len(dp) and dp[:len(sp)] == sp:
        raise PatchError("cannot move a value into its own child")
    resolve_pointer(doc, src)
    if sp == dp:
        return doc
    if not sp:
        return _add(None, path, doc) if not dp else doc
    value = _remove(doc, src)
    return _add(doc, path, value)


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list")
    work = copy.deepcopy(doc)
    try:
        for op in patch:
            work = _apply_one(work, op)
    except PatchError:
        raise
    except (TypeError, ValueError, KeyError, IndexError, AttributeError) as e:
        raise PatchError(str(e)) from e
    if in_place and isinstance(doc, dict) and isinstance(work, dict):
        doc.clear()
        doc.update(work)
        return doc
    if in_place and isinstance(doc, list) and isinstance(work, list):
        doc[:] = work
        return doc
    return work
