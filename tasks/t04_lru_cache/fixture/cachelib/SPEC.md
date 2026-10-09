# LRUCache spec

`LRUCache(capacity: int, ttl: float | None = None, clock=time.monotonic)`

- `get(key, default=None)`: return the value and mark the key as most recently used.
  Expired entries behave as missing and are removed.
- `put(key, value)`: insert or update; updating also marks as most recently used.
  When the cache is over capacity, evict the least recently used entry.
- `delete(key) -> bool`: remove, return whether it existed.
- `__len__`, `__contains__` (contains must not change recency, must respect TTL).
- `stats()` returns `{"hits": int, "misses": int, "evictions": int, "expirations": int}`.
  Expired entries count as a miss and an expiration, not an eviction.
- `capacity <= 0` raises `ValueError`.
- All operations O(1) average. Use `collections.OrderedDict`.
- `clock` is injectable for tests; TTL is measured with it.
