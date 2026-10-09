import export
from export import Exporter, UnknownFormat, export_records, export_to_file, register
from export import registry

R = [{"id": 1, "name": "a"}]


def test_builtin_names():
    assert export.names() == ["csv", "json", "xml"]


def test_unknown_lists_known_names():
    try:
        export_records(R, "yaml")
    except UnknownFormat as e:
        assert "'yaml'" in str(e)
        assert "csv, json, xml" in str(e)
    else:
        raise AssertionError


def test_unknown_file_export_lists_known_names(tmp_path):
    try:
        export_to_file(R, "yaml", tmp_path / "out")
    except UnknownFormat as e:
        assert "csv, json, xml" in str(e)
    else:
        raise AssertionError


def test_new_format_registers_without_core_change(monkeypatch, tmp_path):
    monkeypatch.setattr(registry, "_exporters", dict(registry._exporters))

    @register
    class TxtExporter(Exporter):
        name = "txt"
        extension = ".txt"

        def dump(self, records):
            return "\n".join(str(r) for r in records).encode()

    assert "txt" in export.names()
    assert export_records(R, "txt") == b"{'id': 1, 'name': 'a'}"
    assert export_to_file(R, "txt", tmp_path / "out").endswith(".txt")


def test_duplicate_registration_rejected(monkeypatch):
    monkeypatch.setattr(registry, "_exporters", dict(registry._exporters))

    try:
        @register
        class Dup(Exporter):
            name = "json"
            extension = ".json"

            def dump(self, records):
                return b""
    except ValueError:
        pass
    else:
        raise AssertionError
