from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"


def test_json(tmp_path, capsys):
    import json
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    missing = tmp_path / "nope"
    assert main(["--json", str(p), str(missing)]) == 1
    out, err = capsys.readouterr()
    assert json.loads(out) == {
        "files": [{"path": str(p), "lines": 2, "words": 3, "chars": 16}],
        "total": {"lines": 2, "words": 3, "chars": 16},
    }
    assert "nope" in err
