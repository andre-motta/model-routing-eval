from wc.cli import main


def test_text(tmp_path, capsys):
    p = tmp_path / "a.txt"; p.write_text("hello world\nbye\n")
    assert main([str(p)]) == 0
    assert capsys.readouterr().out == f"       2       3      16 {p}\n"
