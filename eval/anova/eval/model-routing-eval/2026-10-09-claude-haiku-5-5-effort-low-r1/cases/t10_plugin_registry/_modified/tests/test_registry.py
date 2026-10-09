import pytest

import export
from export import Exporter, UnknownFormat, export_records, register

R = [{"id": 1, "name": "a"}]


def test_builtin_formats_registered():
    assert export.names() == ["csv", "json", "xml"]


def test_unknown_format_lists_known_names():
    with pytest.raises(UnknownFormat) as info:
        export_records(R, "yaml")
    assert "csv, json, xml" in str(info.value)


def test_new_format_registers_without_touching_core(monkeypatch):
    monkeypatch.setattr(export.registry, "_exporters", dict(export.registry._exporters))

    @register
    class TxtExporter(Exporter):
        name = "txt"
        extension = ".txt"

        def dump(self, records):
            return b"\n".join(str(r).encode() for r in records)

    assert "txt" in export.names()
    assert export_records(R, "txt") == str(R[0]).encode()


def test_duplicate_name_rejected():
    class Other(Exporter):
        name = "csv"
        extension = ".csv"

        def dump(self, records):
            return b""

    with pytest.raises(ValueError):
        register(Other)
