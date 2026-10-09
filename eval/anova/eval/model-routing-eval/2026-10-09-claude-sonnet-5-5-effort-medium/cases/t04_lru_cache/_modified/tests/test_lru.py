import pytest

from cachelib import LRUCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.mark.parametrize("capacity", [0, -1])
def test_invalid_capacity(capacity):
    with pytest.raises(ValueError):
        LRUCache(capacity)


def test_get_put_and_default():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("missing") is None
    assert c.get("missing", 42) == 42
    assert len(c) == 1


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "b" not in c
    assert "a" in c and "c" in c
    assert c.stats()["evictions"] == 1


def test_update_refreshes_recency_and_does_not_grow():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert len(c) == 2
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


def test_stats_hits_misses():
    c = LRUCache(2)
    c.put("a", 1)
    c.get("a")
    c.get("x")
    assert c.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 0}


def test_ttl_expiry_on_get():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("a", 1)
    clock.now = 9.9
    assert c.get("a") == 1
    clock.now = 10
    assert c.get("a", "gone") == "gone"
    assert len(c) == 0
    assert c.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 1}


def test_contains_respects_ttl():
    clock = FakeClock()
    c = LRUCache(2, ttl=5, clock=clock)
    c.put("a", 1)
    assert "a" in c
    clock.now = 5
    assert "a" not in c


def test_put_resets_ttl():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("a", 1)
    clock.now = 8
    c.put("a", 2)
    clock.now = 15
    assert c.get("a") == 2


def test_no_ttl_never_expires():
    clock = FakeClock()
    c = LRUCache(1, clock=clock)
    c.put("a", 1)
    clock.now = 1e9
    assert c.get("a") == 1
