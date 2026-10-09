import pathlib

from app.config import load_config


def test_types_and_values():
    cfg = load_config("config.toml")
    assert cfg["server"] == {"host": "0.0.0.0", "port": 8080, "debug": False}
    assert cfg["database"] == {"url": "postgresql://localhost/app", "pool_size": 5, "timeout": 2.5}
    assert cfg["features"] == {"beta": True, "max_upload_mb": 25}
    assert isinstance(cfg["server"]["port"], int)
    assert isinstance(cfg["database"]["timeout"], float)
    assert cfg["features"]["beta"] is True


def test_default_path_is_toml_and_ini_removed():
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "config.toml").exists()
    assert not (root / "config.ini").exists()
    assert load_config()["server"]["port"] == 8080
    src = (root / "app" / "config.py").read_text()
    assert "tomllib" in src and "configparser" not in src
