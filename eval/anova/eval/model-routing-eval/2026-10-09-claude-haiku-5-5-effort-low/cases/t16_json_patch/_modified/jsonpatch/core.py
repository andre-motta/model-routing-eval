import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_ARRAY_INDEX = re.compile(r"0|[1-9][0-9]*")
_BAD_ESCAPE = re.compile(r"~(?![01])")
_OPS = {"add", "remove", "replace", "move", "copy", "test"}


def _tokens(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    tokens = []
    for raw in pointer[1:].split("/"):
        if _BAD_ESCAPE.search(raw):
            raise PointerError(f"invalid escape in pointer token {raw!r}")
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tokens


def _array_index(token):
    if not _ARRAY_INDEX.fullmatch(token):
        raise PointerError(f"invalid array index {token!r}")
    return int(token)


def _walk(doc, tokens):
    cur = doc
    for tok in tokens:
        if isinstance(cur, dict):
            if tok not in cur:
                raise PointerError(f"key {tok!r} not found")
            cur = cur[tok]
        elif isinstance(cur, list):
            i = _array_index(tok)
            if i >= len(cur):
                raise PointerError(f"index {i} out of range")
            cur = cur[i]
        else:
            raise PointerError(f"cannot descend into {type(cur).__name__} at {tok!r}")
    return cur


def resolve_pointer(doc, pointer):
    return _walk(doc, _tokens(pointer))


def _json_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        return False
    return type(a) is type(b) and a == b


def _add(doc, path, value):
    tokens = _tokens(path)
    if not tokens:
        return value
    parent = _walk(doc, tokens[:-1])
    key = tokens[-1]
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        if key == "-":
            parent.append(value)
        else:
            i = _array_index(key)
            if i > len(parent):
                raise PointerError(f"index {i} out of range for insert")
            parent.insert(i, value)
    else:
        raise PointerError(f"cannot add into {type(parent).__name__}")
    return doc


def _remove(doc, path):
    tokens = _tokens(path)
    if not tokens:
        raise PatchError("cannot remove the document root")
    parent = _walk(doc, tokens[:-1])
    key = tokens[-1]
    if isinstance(parent, dict):
        if key not in parent:
            raise PointerError(f"key {key!r} not found")
        del parent[key]
    elif isinstance(parent, list):
        i = _array_index(key)
        if i >= len(parent):
            raise PointerError(f"index {i} out of range")
        del parent[i]
    else:
        raise PointerError(f"cannot remove from {type(parent).__name__}")
    return doc


def _replace(doc, path, value):
    tokens = _tokens(path)
    if not tokens:
        return value
    _walk(doc, tokens)  # target must exist
    parent = _walk(doc, tokens[:-1])
    key = tokens[-1]
    if isinstance(parent, dict):
        parent[key] = value
    else:
        parent[_array_index(key)] = value
    return doc


def _require(op, field, kind):
    if field not in op:
        raise PatchError(f"{op['op']} requires {field!r}")
    if not isinstance(op[field], kind):
        raise PatchError(f"{op['op']} field {field!r} has wrong type")
    return op[field]


def _apply_op(doc, op):
    if not isinstance(op, dict):
        raise PatchError("operation must be an object")
    name = op.get("op")
    if not isinstance(name, str) or name not in _OPS:
        raise PatchError(f"unknown op {name!r}")
    path = _require(op, "path", str)

    if name == "add":
        return _add(doc, path, copy.deepcopy(_require_value(op)))
    if name == "replace":
        return _replace(doc, path, copy.deepcopy(_require_value(op)))
    if name == "remove":
        return _remove(doc, path)
    if name == "test":
        expected = _require_value(op)
        if not _json_equal(resolve_pointer(doc, path), expected):
            raise PatchError(f"test failed at {path!r}")
        return doc

    src = _require(op, "from", str)
    if name == "copy":
        value = copy.deepcopy(resolve_pointer(doc, src))
        return _add(doc, path, value)

    # move
    src_tokens = _tokens(src)
    dst_tokens = _tokens(path)
    if len(dst_tokens) > len(src_tokens) and dst_tokens[: len(src_tokens)] == src_tokens:
        raise PatchError(f"cannot move {src!r} into its own child {path!r}")
    value = resolve_pointer(doc, src)
    doc = _remove(doc, src)
    return _add(doc, path, value)


def _require_value(op):
    if "value" not in op:
        raise PatchError(f"{op['op']} requires 'value'")
    return op["value"]


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list of operations")

    # Work on a copy so a failing operation leaves the caller's document untouched.
    work = copy.deepcopy(doc)
    for op in patch:
        work = _apply_op(work, op)

    if not in_place:
        return work
    if isinstance(doc, dict) and isinstance(work, dict):
        doc.clear()
        doc.update(work)
        return doc
    if isinstance(doc, list) and isinstance(work, list):
        doc[:] = work
        return doc
    return work
