import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_INDEX_RE = re.compile(r"(0|[1-9][0-9]*)\Z")


def _parse(pointer):
    if not isinstance(pointer, str):
        raise PointerError("pointer must be a string")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"invalid pointer: {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _index(token, length, allow_end):
    if token == "-" and allow_end:
        return length
    if not _INDEX_RE.match(token):
        raise PointerError(f"invalid array index: {token!r}")
    idx = int(token)
    if idx > length or (idx == length and not allow_end):
        raise PointerError(f"array index out of range: {token!r}")
    return idx


def _walk(doc, tokens):
    for t in tokens:
        if isinstance(doc, dict):
            if t not in doc:
                raise PointerError(f"missing key: {t!r}")
            doc = doc[t]
        elif isinstance(doc, list):
            doc = doc[_index(t, len(doc), False)]
        else:
            raise PointerError(f"cannot descend into scalar at {t!r}")
    return doc


def resolve_pointer(doc, pointer):
    return _walk(doc, _parse(pointer))


def _add(doc, tokens, value):
    if not tokens:
        return value
    parent = _walk(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, dict):
        parent[last] = value
    elif isinstance(parent, list):
        parent.insert(_index(last, len(parent), True), value)
    else:
        raise PointerError("parent is not a container")
    return doc


def _remove(doc, tokens):
    """Return (new_doc, removed_value)."""
    if not tokens:
        raise PatchError("cannot remove the document root")
    parent = _walk(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, dict):
        if last not in parent:
            raise PointerError(f"missing key: {last!r}")
        return doc, parent.pop(last)
    if isinstance(parent, list):
        return doc, parent.pop(_index(last, len(parent), False))
    raise PointerError("parent is not a container")


def _equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        return False
    return type(a) is type(b) or (
        isinstance(a, (int, float)) and isinstance(b, (int, float))
    ) and a == b


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError("operation must be an object")
    name = op.get("op")
    if name not in ("add", "remove", "replace", "move", "copy", "test"):
        raise PatchError(f"unknown op: {name!r}")
    if not isinstance(op.get("path"), str):
        raise PatchError("missing or invalid 'path'")
    tokens = _parse(op["path"])
    if name in ("add", "replace", "test") and "value" not in op:
        raise PatchError("missing 'value'")
    if name in ("move", "copy"):
        if not isinstance(op.get("from"), str):
            raise PatchError("missing or invalid 'from'")
        src = _parse(op["from"])

    if name == "add":
        return _add(doc, tokens, copy.deepcopy(op["value"]))
    if name == "remove":
        return _remove(doc, tokens)[0]
    if name == "replace":
        _walk(doc, tokens)  # must exist
        if not tokens:
            return copy.deepcopy(op["value"])
        doc, _ = _remove(doc, tokens)
        return _add(doc, tokens, copy.deepcopy(op["value"]))
    if name == "test":
        if not _equal(_walk(doc, tokens), op["value"]):
            raise PatchError("test failed")
        return doc
    if name == "copy":
        value = copy.deepcopy(_walk(doc, src))
        return _add(doc, tokens, value)
    # move
    _walk(doc, src)
    if len(src) < len(tokens) and tokens[: len(src)] == src:
        raise PatchError("cannot move a value into its own child")
    if src == tokens:
        return doc
    doc, value = _remove(doc, src)
    return _add(doc, tokens, value)


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list")
    work = copy.deepcopy(doc)
    for op in patch:
        try:
            work = _apply_op(work, op)
        except PatchError:
            raise
        except (TypeError, ValueError, KeyError, IndexError) as e:
            raise PatchError(str(e)) from e
    if in_place:
        if isinstance(doc, dict) and isinstance(work, dict):
            doc.clear()
            doc.update(work)
            return doc
        if isinstance(doc, list) and isinstance(work, list):
            doc[:] = work
            return doc
    return work
