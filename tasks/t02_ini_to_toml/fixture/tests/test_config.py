from app.config import load_config


def test_sections():
    cfg = load_config()
    assert set(cfg) == {"server", "database", "features"}
    assert cfg["server"]["host"] == "0.0.0.0"
