`export/core.py` dispatches on format strings with if-chains in three places. Refactor
it into a plugin architecture:

- an `Exporter` base class (or protocol) with `name`, `extension`, `dump(records) -> bytes`
- a registry with `register(exporter_cls)` usable as a decorator, `get(name)`, `names()`
- the three existing formats (csv, json, xml) move into `export/formats/` as separate
  modules, auto-discovered or imported by the package so they are registered on
  `import export`
- `export_records(records, fmt)` and `export_to_file(records, fmt, path)` keep their
  signatures and behaviour
- unknown format raises `export.UnknownFormat` with the list of known names in the message
- adding a new format must require no change to `core.py`

Keep the existing tests passing and run them.
