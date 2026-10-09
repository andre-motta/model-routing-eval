import pytest

from cachelib.lru import LRUCache


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_rejects_non_positive_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-1)


def test_put_and_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1
    assert len(cache) == 1


def test_get_missing_returns_default():
    cache = LRUCache(2)
    assert cache.get("nope") is None
    assert cache.get("nope", "fallback") == "fallback"


def test_evicts_least_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert cache.stats()["evictions"] == 1


def test_get_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert "a" in cache
    assert "b" not in cache


def test_put_existing_key_updates_value_and_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert "b" not in cache
    assert len(cache) == 2
    assert cache.stats()["evictions"] == 1


def test_delete_returns_whether_key_existed():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.delete("a") is True
    assert cache.delete("a") is False
    assert "a" not in cache
    assert len(cache) == 0


def test_contains_does_not_change_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache


def test_contains_does_not_count_as_hit_or_miss():
    cache = LRUCache(2)
    cache.put("a", 1)
    _ = "a" in cache
    _ = "z" in cache
    stats = cache.stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0


def test_stats_counts_hits_and_misses():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("missing")
    assert cache.stats() == {"hits": 2, "misses": 1, "evictions": 0, "expirations": 0}


def test_ttl_expires_entry_on_get():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(9.9)
    assert cache.get("a") == 1
    clock.advance(0.1)
    assert cache.get("a") is None
    assert "a" not in cache
    assert len(cache) == 0


def test_expired_get_counts_as_miss_and_expiration_not_eviction():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    cache.get("a")
    assert cache.stats() == {"hits": 0, "misses": 1, "evictions": 0, "expirations": 1}


def test_contains_respects_ttl_and_counts_expiration():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(6)
    assert "a" not in cache
    stats = cache.stats()
    assert stats["expirations"] == 1
    assert stats["evictions"] == 0


def test_put_resets_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(8)
    cache.put("a", 2)
    clock.advance(8)
    assert cache.get("a") == 2


def test_no_ttl_never_expires():
    clock = FakeClock()
    cache = LRUCache(2, clock=clock)
    cache.put("a", 1)
    clock.advance(10**9)
    assert cache.get("a") == 1
    assert cache.stats()["expirations"] == 0


def test_capacity_one():
    cache = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert len(cache) == 1
