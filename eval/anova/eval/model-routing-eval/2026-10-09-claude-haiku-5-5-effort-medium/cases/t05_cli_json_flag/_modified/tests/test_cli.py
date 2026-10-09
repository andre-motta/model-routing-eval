import json

from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"


def test_text_multiple_files_total(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p), str(p)]) == 0
    assert capsys.readouterr().out == (
        f"       2       3      16 {p}\n"
        f"       2       3      16 {p}\n"
        "       4       6      32 total\n"
    )


def test_text_missing_file(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    missing = tmp_path / "nope.txt"
    assert main([str(p), str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        f"       2       3      16 {p}\n"
        "       2       3      16 total\n"
    )
    assert captured.err.startswith(f"wc: {missing}: ")


def test_json(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main(["--json", str(p)]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }
    assert captured.err == ""


def test_json_multiple_files(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    q = tmp_path / "b.txt"; q.write_text("one two three")
    assert main(["--json", str(p), str(q)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "files": [
            {"path": str(p), "lines": 2, "words": 3, "chars": 16},
            {"path": str(q), "lines": 0, "words": 3, "chars": 13},
        ],
        "total": {"lines": 2, "words": 6, "chars": 29},
    }


def test_json_missing_file(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    missing = tmp_path / "nope.txt"
    assert main(["--json", str(missing), str(p)]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }
    assert captured.err.startswith(f"wc: {missing}: ")
