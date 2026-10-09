# Spec

## JSON Pointer (RFC 6901)

`resolve_pointer(doc, pointer) -> value`

- `""` is the whole document. Otherwise the pointer starts with `/` and each token is
  unescaped: `~1` -> `/`, `~0` -> `~` (in that order).
- Object tokens are keys. Array tokens must be a non-negative integer with no leading
  zeros (`"0"` ok, `"01"` not ok); `"-"` is only valid for `add` as "append".
- Anything invalid raises `PointerError` (subclass of `PatchError`).

## JSON Patch (RFC 6902)

`apply_patch(doc, patch, in_place=False) -> new_doc`

`patch` is a list of operation dicts with `op` in `add`, `remove`, `replace`, `move`,
`copy`, `test`, plus `path` and, where applicable, `value` or `from`.

- `add`: object key set or array insert at index (index == len allowed, `-` appends);
  replacing the root is allowed.
- `remove`: target must exist.
- `replace`: target must exist.
- `move`: `from` must exist; `from` must not be a proper prefix of `path` (cannot move a
  value into one of its own children); equivalent to remove then add.
- `copy`: `from` must exist; deep copy; then add.
- `test`: deep equality of `value` with the target. Numbers compare by value
  (`1 == 1.0`), but `True != 1`.
- Operations apply in order. If any operation fails, raise `PatchError` and leave the
  input document unchanged (atomic). With `in_place=True` the input document is mutated
  on success and untouched on failure; otherwise the input is never mutated.
- Unknown `op`, missing required fields, or wrong types raise `PatchError`.
