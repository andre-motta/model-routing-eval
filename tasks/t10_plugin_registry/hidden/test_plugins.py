import importlib
import inspect
import json
import pathlib

import pytest

import export
from export import export_records, export_to_file, UnknownFormat

R = [{"id": 1, "name": "a&b"}, {"id": 2, "name": "c"}]


def test_behaviour_preserved(tmp_path):
    assert export_records(R, "csv") == b"id,name\n1,a&b\n2,c\n"
    assert json.loads(export_records(R, "json")) == R
    assert b"<name>a&amp;b</name>" in export_records(R, "xml")
    assert export_to_file(R, "xml", tmp_path / "o").endswith(".xml")
    assert export_records([], "csv") == b""


def test_registry_api_and_discovery():
    reg = _registry()
    assert set(reg.names()) >= {"csv", "json", "xml"}
    assert reg.get("csv").extension == ".csv"
    pkg = pathlib.Path(export.__file__).parent
    assert (pkg / "formats").is_dir()
    mods = [p.stem for p in (pkg / "formats").glob("*.py") if p.stem != "__init__"]
    assert len(mods) >= 3, f"expected one module per format under formats/, found {mods}"
    for fmt in ("csv", "json", "xml"):
        assert any(fmt in m for m in mods), f"no module for {fmt} under formats/: {mods}"


def test_unknown_lists_known():
    with pytest.raises(UnknownFormat) as e:
        export_records(R, "yaml")
    msg = str(e.value)
    assert "csv" in msg and "json" in msg and "xml" in msg


def test_new_format_without_touching_core():
    reg = _registry()
    base = _base()

    @reg.register
    class TSV(base):
        name = "tsv"
        extension = ".tsv"

        def dump(self, records):
            if not records:
                return b""
            head = "\t".join(records[0].keys())
            rows = ["\t".join(str(v) for v in r.values()) for r in records]
            return ("\n".join([head] + rows) + "\n").encode()

    assert export_records(R, "tsv") == b"id\tname\n1\ta&b\n2\tc\n"
    core_src = (pathlib.Path(export.__file__).parent / "core.py").read_text()
    for fmt in ("csv", "json", "xml"):
        assert f'"{fmt}"' not in core_src and f"'{fmt}'" not in core_src, f"core.py still hardcodes {fmt}"


def _usable(obj):
    """A registry is anything (instance, or class with classmethods) whose names() works without self."""
    if obj is None or not all(hasattr(obj, a) for a in ("register", "get", "names")):
        return False
    try:
        obj.names()
    except TypeError:
        return False
    return True


def _registry():
    seen = []
    for modname in ("export", "export.registry", "export.core", "export.plugins", "export.base", "export.exporters"):
        try:
            m = importlib.import_module(modname)
        except ImportError:
            continue
        seen.append(m)
    for m in seen:
        for name in ("registry", "REGISTRY", "Registry", "exporters", "EXPORTERS"):
            if _usable(getattr(m, name, None)):
                return getattr(m, name)
    for m in seen:
        for _, obj in inspect.getmembers(m):
            if _usable(obj):
                return obj
    raise AssertionError("no registry object found with register/get/names")


def _base():
    for modname in ("export", "export.base", "export.core", "export.registry", "export.plugins"):
        try:
            m = importlib.import_module(modname)
        except ImportError:
            continue
        obj = getattr(m, "Exporter", None)
        if obj is not None:
            return obj
    raise AssertionError("no Exporter base class found")
