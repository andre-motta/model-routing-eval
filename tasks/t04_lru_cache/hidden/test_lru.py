import pytest

from cachelib import LRUCache


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_basic_and_eviction_order():
    c = LRUCache(2)
    c.put("a", 1); c.put("b", 2)
    assert c.get("a") == 1          # a is now most recent
    c.put("c", 3)                    # evicts b
    assert "b" not in c and "a" in c and "c" in c
    assert len(c) == 2
    assert c.stats()["evictions"] == 1


def test_update_marks_recent():
    c = LRUCache(2)
    c.put("a", 1); c.put("b", 2); c.put("a", 10)
    c.put("c", 3)
    assert c.get("a") == 10 and "b" not in c


def test_contains_does_not_touch_recency():
    c = LRUCache(2)
    c.put("a", 1); c.put("b", 2)
    assert "a" in c
    c.put("c", 3)
    assert "a" not in c


def test_ttl_expiry_counts():
    clk = Clock()
    c = LRUCache(10, ttl=5, clock=clk)
    c.put("a", 1)
    clk.t = 4.9
    assert c.get("a") == 1
    clk.t = 5.1
    assert c.get("a", "gone") == "gone"
    assert "a" not in c
    s = c.stats()
    assert s["hits"] == 1 and s["misses"] == 1 and s["expirations"] == 1 and s["evictions"] == 0
    assert len(c) == 0


def test_delete_and_capacity_validation():
    c = LRUCache(1)
    c.put("a", 1)
    assert c.delete("a") is True and c.delete("a") is False
    with pytest.raises(ValueError):
        LRUCache(0)
