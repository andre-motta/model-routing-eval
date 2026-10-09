import json

from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"


def test_json_single(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main(["--json", str(p)]) == 0
    out = json.loads(capsys.readouterr().out)
    one = {"lines": 2, "words": 3, "chars": 16}
    assert out == {"files": [{"path": str(p), **one}], "total": one}


def test_json_multiple_with_missing(tmp_path, capsys):
    a = tmp_path / "a.txt"; a.write_text("one two\n")
    b = tmp_path / "b.txt"; b.write_text("three\n")
    missing = tmp_path / "nope.txt"
    assert main(["--json", str(a), str(missing), str(b)]) == 1
    cap = capsys.readouterr()
    assert f"wc: {missing}: " in cap.err
    out = json.loads(cap.out)
    assert [f["path"] for f in out["files"]] == [str(a), str(b)]
    assert out["total"] == {"lines": 2, "words": 3, "chars": 14}


def test_missing_text_exit_code(tmp_path, capsys):
    missing = tmp_path / "nope.txt"
    assert main([str(missing)]) == 1
    cap = capsys.readouterr()
    assert cap.out == ""
    assert f"wc: {missing}: " in cap.err
