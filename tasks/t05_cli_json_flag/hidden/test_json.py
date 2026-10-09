import json
import subprocess
import sys

from wc.cli import main


def test_text_unchanged(tmp_path, capsys):
    a = tmp_path / "a.txt"; a.write_text("hello world\nbye\n")
    b = tmp_path / "b.txt"; b.write_text("x\n")
    assert main([str(a), str(b)]) == 0
    out = capsys.readouterr().out
    assert out == f"       2       3      16 {a}\n       1       1       2 {b}\n       3       4      18 total\n"


def test_json_shape(tmp_path, capsys):
    a = tmp_path / "a.txt"; a.write_text("hello world\nbye\n")
    b = tmp_path / "b.txt"; b.write_text("x\n")
    assert main(["--json", str(a), str(b)]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d == {"files": [{"path": str(a), "lines": 2, "words": 3, "chars": 16},
                           {"path": str(b), "lines": 1, "words": 1, "chars": 2}],
                 "total": {"lines": 3, "words": 4, "chars": 18}}


def test_json_missing_file(tmp_path, capsys):
    a = tmp_path / "a.txt"; a.write_text("x\n")
    assert main(["--json", str(a), str(tmp_path / "nope")]) == 1
    cap = capsys.readouterr()
    d = json.loads(cap.out)
    assert [f["path"] for f in d["files"]] == [str(a)]
    assert "nope" in cap.err


def test_module_entrypoint(tmp_path):
    a = tmp_path / "a.txt"; a.write_text("one two\n")
    p = subprocess.run([sys.executable, "-m", "wc", "--json", str(a)], capture_output=True, text=True)
    assert p.returncode == 0 and json.loads(p.stdout)["total"]["words"] == 2
