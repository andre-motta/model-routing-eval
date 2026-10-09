import copy
import re


class PatchError(Exception):
    pass


class PointerError(PatchError):
    pass


_ARRAY_INDEX = re.compile(r"^(0|[1-9][0-9]*)$")


def _split_pointer(pointer):
    if not isinstance(pointer, str):
        raise PointerError(f"pointer must be a string, got {type(pointer).__name__}")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerError(f"pointer must be empty or start with '/': {pointer!r}")
    tokens = []
    for raw in pointer[1:].split("/"):
        tokens.append(_unescape(raw, pointer))
    return tokens


def _unescape(token, pointer):
    out = []
    i = 0
    while i < len(token):
        ch = token[i]
        if ch == "~":
            nxt = token[i + 1 : i + 2]
            if nxt == "0":
                out.append("~")
            elif nxt == "1":
                out.append("/")
            else:
                raise PointerError(f"invalid escape in pointer {pointer!r}")
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _index(token, container, pointer):
    if not _ARRAY_INDEX.match(token):
        raise PointerError(f"invalid array index {token!r} in pointer {pointer!r}")
    return int(token)


def _child(container, token, pointer):
    if isinstance(container, dict):
        if token not in container:
            raise PointerError(f"key {token!r} not found in pointer {pointer!r}")
        return container[token]
    if isinstance(container, list):
        idx = _index(token, container, pointer)
        if idx >= len(container):
            raise PointerError(f"index {idx} out of range in pointer {pointer!r}")
        return container[idx]
    raise PointerError(f"cannot descend into scalar in pointer {pointer!r}")


def resolve_pointer(doc, pointer):
    node = doc
    for token in _split_pointer(pointer):
        node = _child(node, token, pointer)
    return node


def _parent_and_key(doc, pointer):
    tokens = _split_pointer(pointer)
    if not tokens:
        raise PointerError("operation requires a non-root pointer")
    node = doc
    for token in tokens[:-1]:
        node = _child(node, token, pointer)
    return node, tokens[-1]


def _add(doc, path, value):
    if path == "":
        return value
    parent, key = _parent_and_key(doc, path)
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        if key == "-":
            parent.append(value)
        else:
            idx = _index(key, parent, path)
            if idx > len(parent):
                raise PointerError(f"index {idx} out of range in pointer {path!r}")
            parent.insert(idx, value)
    else:
        raise PointerError(f"cannot add into scalar at pointer {path!r}")
    return doc


def _remove(doc, path):
    if path == "":
        raise PatchError("cannot remove the document root")
    parent, key = _parent_and_key(doc, path)
    if isinstance(parent, dict):
        if key not in parent:
            raise PointerError(f"key {key!r} not found in pointer {path!r}")
        del parent[key]
    elif isinstance(parent, list):
        idx = _index(key, parent, path)
        if idx >= len(parent):
            raise PointerError(f"index {idx} out of range in pointer {path!r}")
        del parent[idx]
    else:
        raise PointerError(f"cannot remove from scalar at pointer {path!r}")
    return doc


def _replace(doc, path, value):
    resolve_pointer(doc, path)  # target must exist
    if path == "":
        return value
    parent, key = _parent_and_key(doc, path)
    if isinstance(parent, dict):
        parent[key] = value
    else:
        parent[_index(key, parent, path)] = value
    return doc


def _json_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if type(a) is not type(b):
        return False
    return a == b


def _require(op_dict, field, kind, index):
    if field not in op_dict:
        raise PatchError(f"operation {index} ({op_dict.get('op')}) missing '{field}'")
    value = op_dict[field]
    if not isinstance(value, kind):
        raise PatchError(f"operation {index} '{field}' must be {kind.__name__}")
    return value


def _apply_op(doc, op_dict, index):
    if not isinstance(op_dict, dict):
        raise PatchError(f"operation {index} must be an object")
    op = _require(op_dict, "op", str, index)
    path = _require(op_dict, "path", str, index)

    if op in ("add", "replace", "test"):
        if "value" not in op_dict:
            raise PatchError(f"operation {index} ({op}) missing 'value'")
        value = op_dict["value"]
        if op == "add":
            return _add(doc, path, copy.deepcopy(value))
        if op == "replace":
            return _replace(doc, path, copy.deepcopy(value))
        actual = resolve_pointer(doc, path)
        if not _json_equal(actual, value):
            raise PatchError(f"test failed at {path!r}")
        return doc

    if op == "remove":
        return _remove(doc, path)

    if op in ("move", "copy"):
        src = _require(op_dict, "from", str, index)
        if op == "move" and path != src and path.startswith(src + "/"):
            raise PatchError(f"cannot move {src!r} into its own child {path!r}")
        value = copy.deepcopy(resolve_pointer(doc, src))
        if op == "move":
            doc = _remove(doc, src)
        return _add(doc, path, value)

    raise PatchError(f"unknown op {op!r} in operation {index}")


def apply_patch(doc, patch, in_place=False):
    if not isinstance(patch, list):
        raise PatchError("patch must be a list of operations")

    # Work on a copy so a failure part-way through leaves the input untouched.
    work = copy.deepcopy(doc)
    for index, op_dict in enumerate(patch):
        work = _apply_op(work, op_dict, index)

    if not in_place:
        return work

    if isinstance(doc, dict) and isinstance(work, dict):
        doc.clear()
        doc.update(work)
        return doc
    if isinstance(doc, list) and isinstance(work, list):
        doc[:] = work
        return doc
    # Scalar or replaced root: nothing to mutate in place, return the new value.
    return work
