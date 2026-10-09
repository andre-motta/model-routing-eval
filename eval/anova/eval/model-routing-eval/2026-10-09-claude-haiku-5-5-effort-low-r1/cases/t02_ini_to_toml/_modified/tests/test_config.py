from app.config import load_config


def test_sections():
    cfg = load_config()
    assert set(cfg) == {"server", "database", "features"}
    assert cfg["server"]["host"] == "0.0.0.0"


def test_types():
    cfg = load_config()
    assert cfg["server"]["port"] == 8080
    assert isinstance(cfg["server"]["port"], int)
    assert cfg["server"]["debug"] is False
    assert isinstance(cfg["database"]["timeout"], float)
    assert cfg["database"]["timeout"] == 2.5
    assert cfg["features"]["beta"] is True
    assert isinstance(cfg["features"]["max_upload_mb"], int)
