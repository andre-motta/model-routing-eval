from app.config import load_config


def test_sections():
    cfg = load_config()
    assert set(cfg) == {"server", "database", "features"}
    assert cfg["server"]["host"] == "0.0.0.0"


def test_value_types():
    cfg = load_config()
    assert cfg["server"]["port"] == 8080 and isinstance(cfg["server"]["port"], int)
    assert cfg["server"]["debug"] is False
    assert cfg["database"]["pool_size"] == 5 and isinstance(cfg["database"]["pool_size"], int)
    assert cfg["database"]["timeout"] == 2.5 and isinstance(cfg["database"]["timeout"], float)
    assert cfg["features"]["beta"] is True
    assert cfg["features"]["max_upload_mb"] == 25 and isinstance(cfg["features"]["max_upload_mb"], int)
