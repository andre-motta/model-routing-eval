import json

from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"


def test_text_missing_file(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    missing = tmp_path / "nope.txt"
    assert main([str(p), str(missing)]) == 1
    captured = capsys.readouterr()
    assert f"wc: {missing}: " in captured.err
    assert captured.out == f"       2       3      16 {p}\n       2       3      16 total\n"


def test_json(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main(["--json", str(p)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }


def test_json_multiple_files(tmp_path, capsys):
    a = tmp_path / "a.txt"; a.write_text("hello world\nbye\n")
    b = tmp_path / "b.txt"; b.write_text("one two three")
    assert main(["--json", str(a), str(b)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "files": [
            {"path": str(a), "lines": 2, "words": 3, "chars": 16},
            {"path": str(b), "lines": 0, "words": 3, "chars": 13},
        ],
        "total": {"lines": 2, "words": 6, "chars": 29},
    }


def test_json_missing_file(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    missing = tmp_path / "nope.txt"
    assert main(["--json", str(p), str(missing)]) == 1
    captured = capsys.readouterr()
    assert f"wc: {missing}: " in captured.err
    assert json.loads(captured.out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }
