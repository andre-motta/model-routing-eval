import json

from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"


def test_json(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main(["--json", str(p)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }


def test_json_missing_file(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hi\n")
    missing = str(tmp_path / "nope")
    assert main(["--json", str(p), missing]) == 1
    cap = capsys.readouterr()
    assert "nope" in cap.err
    out = json.loads(cap.out)
    assert [f["path"] for f in out["files"]] == [str(p)]
    assert out["total"] == {"lines": 1, "words": 1, "chars": 3}


def test_text_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "nope")]) == 1
    assert "nope" in capsys.readouterr().err
