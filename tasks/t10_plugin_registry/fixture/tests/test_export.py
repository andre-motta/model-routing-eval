import json

from export import export_records, export_to_file, UnknownFormat

R = [{"id": 1, "name": "a&b"}, {"id": 2, "name": "c"}]


def test_csv():
    assert export_records(R, "csv") == b"id,name\n1,a&b\n2,c\n"


def test_json():
    assert json.loads(export_records(R, "json")) == R


def test_xml():
    assert b"<name>a&amp;b</name>" in export_records(R, "xml")


def test_file_extension(tmp_path):
    p = export_to_file(R, "json", tmp_path / "out")
    assert p.endswith(".json")


def test_unknown():
    try:
        export_records(R, "yaml")
    except UnknownFormat:
        pass
    else:
        raise AssertionError
