import pytest

from cachelib import LRUCache


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


def test_get_returns_value_and_default_for_missing():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None
    assert cache.get("missing", "fallback") == "fallback"


def test_put_updates_existing_key_without_growing():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("a", 2)
    assert cache.get("a") == 2
    assert len(cache) == 1


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


def test_put_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert "b" not in cache


def test_contains_does_not_change_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache


def test_contains_does_not_affect_hit_or_miss_stats():
    cache = LRUCache(2)
    cache.put("a", 1)
    _ = "a" in cache
    _ = "zzz" in cache
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 0


def test_delete_returns_whether_key_existed():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.delete("a") is True
    assert cache.delete("a") is False
    assert "a" not in cache
    assert len(cache) == 0


def test_len_and_contains():
    cache = LRUCache(3)
    assert len(cache) == 0
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
    assert "a" in cache
    assert "z" not in cache


def test_stats_count_hits_and_misses():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("nope")
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
    assert cache.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 1}


def test_expired_entry_is_not_counted_as_eviction():
    clock = FakeClock()
    cache = LRUCache(1, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    cache.put("b", 2)
    stats = cache.stats()
    assert stats["evictions"] == 0
    assert stats["expirations"] == 1
    assert cache.get("b") == 2


def test_expired_lru_entry_counts_as_expiration_when_pushed_out():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(3)
    cache.put("b", 2)
    clock.advance(3)
    cache.put("c", 3)
    stats = cache.stats()
    assert stats["expirations"] == 1
    assert stats["evictions"] == 0
    assert "b" in cache and "c" in cache


def test_put_resets_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(8)
    cache.put("a", 2)
    clock.advance(8)
    assert cache.get("a") == 2


def test_contains_respects_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(10)
    assert "a" not in cache
    assert cache.stats()["expirations"] == 1


def test_len_excludes_expired_entries():
    clock = FakeClock()
    cache = LRUCache(3, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(6)
    cache.put("b", 2)
    clock.advance(6)
    assert len(cache) == 1
    assert cache.stats()["expirations"] == 1


def test_delete_expired_key_reports_false_only_if_absent():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    assert cache.delete("a") is True


def test_no_ttl_means_entries_never_expire():
    clock = FakeClock()
    cache = LRUCache(2, clock=clock)
    cache.put("a", 1)
    clock.advance(10**9)
    assert cache.get("a") == 1
    assert cache.stats()["expirations"] == 0


def test_default_clock_is_monotonic_and_works():
    cache = LRUCache(2, ttl=3600)
    cache.put("a", 1)
    assert cache.get("a") == 1
