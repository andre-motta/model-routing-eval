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


def test_get_returns_value_and_default_for_missing():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None
    assert cache.get("missing", "dflt") == "dflt"


def test_get_refreshes_recency_so_other_key_is_evicted():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # "b" is now least recently used
    cache.put("c", 3)
    assert "a" in cache
    assert "b" not in cache
    assert "c" in cache


def test_put_existing_key_updates_value_and_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)  # update makes "b" the LRU entry
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert "b" not in cache
    assert len(cache) == 2


def test_eviction_counts_and_len_capped_at_capacity():
    cache = LRUCache(2)
    for i in range(5):
        cache.put(i, i)
    assert len(cache) == 2
    assert cache.stats()["evictions"] == 3
    assert 3 in cache and 4 in cache


def test_delete_returns_whether_key_existed():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.delete("a") is True
    assert cache.delete("a") is False
    assert "a" not in cache
    assert len(cache) == 0


def test_stats_track_hits_and_misses():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("b")
    assert cache.stats() == {"hits": 1, "misses": 1, "evictions": 0, "expirations": 0}


def test_contains_does_not_change_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache  # must not refresh "a"
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache


def test_contains_does_not_touch_hit_or_miss_stats():
    cache = LRUCache(2)
    cache.put("a", 1)
    _ = "a" in cache
    _ = "b" in cache
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 0


def test_ttl_expired_entry_behaves_as_missing_and_counts_as_expiration():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(9.9)
    assert cache.get("a") == 1
    clock.advance(0.2)
    assert cache.get("a", "gone") == "gone"
    stats = cache.stats()
    assert stats["misses"] == 1
    assert stats["expirations"] == 1
    assert stats["evictions"] == 0
    assert len(cache) == 0


def test_ttl_contains_respects_expiry():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    assert "a" not in cache
    assert cache.stats()["expirations"] == 1


def test_ttl_delete_of_expired_entry_returns_false():
    clock = FakeClock()
    cache = LRUCache(2, ttl=5, clock=clock)
    cache.put("a", 1)
    clock.advance(5)
    assert cache.delete("a") is False


def test_put_resets_ttl_on_update():
    clock = FakeClock()
    cache = LRUCache(2, ttl=10, clock=clock)
    cache.put("a", 1)
    clock.advance(8)
    cache.put("a", 2)
    clock.advance(8)
    assert cache.get("a") == 2


def test_no_ttl_entries_never_expire():
    clock = FakeClock()
    cache = LRUCache(2, clock=clock)
    cache.put("a", 1)
    clock.advance(1_000_000)
    assert cache.get("a") == 1
    assert cache.stats()["expirations"] == 0
