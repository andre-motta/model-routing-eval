import pytest

from cachelib import LRUCache


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_capacity_must_be_positive():
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
    assert cache.get("nope", default=42) == 42


def test_falsy_values_are_hits():
    cache = LRUCache(2)
    cache.put("zero", 0)
    cache.put("none", None)
    assert cache.get("zero", default="x") == 0
    assert cache.get("none", default="x") is None
    assert cache.stats()["hits"] == 2
    assert cache.stats()["misses"] == 0


def test_get_refreshes_recency_so_other_key_is_evicted():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert "a" in cache
    assert "b" not in cache
    assert "c" in cache


def test_put_update_refreshes_recency_and_does_not_grow():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    assert len(cache) == 2
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert cache.get("b") is None
    assert cache.stats()["evictions"] == 1


def test_eviction_is_least_recently_used():
    cache = LRUCache(3)
    for key in "abc":
        cache.put(key, key)
    cache.put("d", "d")
    assert "a" not in cache
    assert all(k in cache for k in "bcd")
    assert len(cache) == 3
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


def test_contains_does_not_count_hits_or_misses():
    cache = LRUCache(2)
    cache.put("a", 1)
    _ = "a" in cache
    _ = "z" in cache
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 0


def test_stats_counts_hits_and_misses():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("b")
    assert cache.stats() == {"hits": 2, "misses": 1, "evictions": 0, "expirations": 0}


def test_stats_returns_a_copy():
    cache = LRUCache(2)
    snapshot = cache.stats()
    snapshot["hits"] = 99
    assert cache.stats()["hits"] == 0


def test_ttl_entry_expires_and_behaves_as_miss():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(9.9)
    assert cache.get("a") == 1
    clock.advance(0.1)
    assert cache.get("a", default="gone") == "gone"
    assert len(cache) == 0
    assert cache.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 1}


def test_expired_get_removes_entry():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    cache.get("a")
    assert len(cache) == 0
    assert cache.stats()["expirations"] == 1


def test_contains_respects_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    assert "a" in cache
    clock.advance(5)
    assert "a" not in cache
    assert len(cache) == 0
    assert cache.stats()["expirations"] == 1
    assert cache.stats()["misses"] == 0


def test_put_refreshes_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(4)
    cache.put("a", 2)
    clock.advance(4)
    assert cache.get("a") == 2


def test_get_does_not_extend_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(3)
    assert cache.get("a") == 1
    clock.advance(3)
    assert cache.get("a") is None


def test_delete_expired_entry_returns_false_and_counts_expiration():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    assert cache.delete("a") is False
    assert len(cache) == 0
    assert cache.stats()["expirations"] == 1
    assert cache.stats()["evictions"] == 0


def test_no_ttl_entries_never_expire():
    clock = FakeClock()
    cache = LRUCache(2, clock=clock)
    cache.put("a", 1)
    clock.advance(10**9)
    assert cache.get("a") == 1
    assert cache.stats()["expirations"] == 0


def test_expired_lru_entry_pushed_out_counts_as_expiration_not_eviction():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("old", 1)
    clock.advance(5)
    cache.put("new1", 2)
    cache.put("new2", 3)
    assert "old" not in cache
    assert cache.stats()["expirations"] == 1
    assert cache.stats()["evictions"] == 0


def test_live_lru_entry_pushed_out_counts_as_eviction_with_ttl():
    clock = FakeClock()
    cache = LRUCache(2, ttl=100, clock=clock)
    cache.put("a", 1)
    clock.advance(1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.stats()["evictions"] == 1
    assert cache.stats()["expirations"] == 0


def test_capacity_one():
    cache = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert cache.stats()["evictions"] == 1


def test_many_operations_stay_within_capacity():
    cache = LRUCache(50)
    for i in range(1000):
        cache.put(i, i)
        assert len(cache) <= 50
    assert len(cache) == 50
    assert cache.stats()["evictions"] == 950
    assert all(i in cache for i in range(950, 1000))
