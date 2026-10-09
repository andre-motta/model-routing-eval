import pytest

from cachelib.lru import LRUCache


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_invalid_capacity():
    for c in (0, -1):
        with pytest.raises(ValueError):
            LRUCache(c)


def test_basic_get_put_delete():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("x", "d") == "d"
    assert c.delete("a") is True
    assert c.delete("a") is False
    assert len(c) == 0


def test_eviction_order_and_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "b" not in c and "a" in c and "c" in c
    assert c.stats()["evictions"] == 1


def test_update_refreshes_recency_without_eviction():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    c.put("c", 3)
    assert c.get("a") == 10
    assert "b" not in c
    assert c.stats()["evictions"] == 1


def test_contains_does_not_change_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)
    assert "a" not in c


def test_ttl_expiry():
    clk = Clock()
    c = LRUCache(2, ttl=10, clock=clk)
    c.put("a", 1)
    clk.t = 5
    assert c.get("a") == 1
    clk.t = 10
    assert c.get("a") is None
    assert len(c) == 0
    s = c.stats()
    assert s == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 1}


def test_contains_respects_ttl():
    clk = Clock()
    c = LRUCache(2, ttl=1, clock=clk)
    c.put("a", 1)
    clk.t = 2
    assert "a" not in c


def test_put_refreshes_ttl():
    clk = Clock()
    c = LRUCache(2, ttl=10, clock=clk)
    c.put("a", 1)
    clk.t = 8
    c.put("a", 2)
    clk.t = 15
    assert c.get("a") == 2


def test_stats_hits_misses():
    c = LRUCache(1)
    c.put("a", 1)
    c.get("a")
    c.get("b")
    assert c.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 0}
