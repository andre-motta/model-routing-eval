import pytest

import export
from export import registry
from export.base import Exporter

R = [{"id": 1, "name": "a"}]


def test_builtin_formats_registered():
    assert export.names() == ["csv", "json", "xml"]


def test_unknown_format_lists_known_names():
    with pytest.raises(export.UnknownFormat) as info:
        export.get("yaml")
    assert "csv, json, xml" in str(info.value)


def test_plugin_registered_without_touching_core(monkeypatch, tmp_path):
    monkeypatch.setattr(registry, "_exporters", dict(registry._exporters))

    @export.register
    class TxtExporter(Exporter):
        name = "txt"
        extension = ".txt"

        def dump(self, records):
            return b"\n".join(str(r).encode() for r in records)

    assert "txt" in export.names()
    assert export.export_records(R, "txt") == b"{'id': 1, 'name': 'a'}"
    p = export.export_to_file(R, "txt", tmp_path / "out")
    assert p.endswith(".txt")
    assert (tmp_path / "out.txt").read_bytes() == b"{'id': 1, 'name': 'a'}"


def test_duplicate_registration_rejected(monkeypatch):
    monkeypatch.setattr(registry, "_exporters", dict(registry._exporters))

    with pytest.raises(ValueError):

        @export.register
        class Dup(Exporter):
            name = "json"
            extension = ".json"

            def dump(self, records):
                return b""
