import pytest

from cachelib.lru import LRUCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_invalid_capacity():
    for cap in (0, -1):
        with pytest.raises(ValueError):
            LRUCache(cap)


def test_basic_get_put_and_default():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("x") is None
    assert c.get("x", 7) == 7
    assert len(c) == 1


def test_eviction_order_and_get_refreshes():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "b" not in c
    assert "a" in c and "c" in c
    assert c.stats()["evictions"] == 1


def test_update_refreshes_and_does_not_evict():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert c.stats()["evictions"] == 0
    c.put("c", 3)
    assert "b" not in c
    assert c.get("a") == 10


def test_contains_does_not_change_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)
    assert "a" not in c


def test_delete():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.delete("a") is True
    assert c.delete("a") is False
    assert len(c) == 0


def test_ttl_expiry_in_get():
    clk = FakeClock()
    c = LRUCache(2, ttl=10, clock=clk)
    c.put("a", 1)
    clk.now = 9
    assert c.get("a") == 1
    clk.now = 10
    assert c.get("a", "d") == "d"
    assert len(c) == 0
    assert c.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 1}


def test_ttl_contains_respects_expiry():
    clk = FakeClock()
    c = LRUCache(2, ttl=5, clock=clk)
    c.put("a", 1)
    assert "a" in c
    clk.now = 6
    assert "a" not in c
    assert len(c) == 0


def test_put_resets_ttl():
    clk = FakeClock()
    c = LRUCache(2, ttl=10, clock=clk)
    c.put("a", 1)
    clk.now = 8
    c.put("a", 2)
    clk.now = 15
    assert c.get("a") == 2


def test_stats_hits_misses():
    c = LRUCache(1)
    c.put("a", 1)
    c.get("a")
    c.get("b")
    assert c.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 0}
