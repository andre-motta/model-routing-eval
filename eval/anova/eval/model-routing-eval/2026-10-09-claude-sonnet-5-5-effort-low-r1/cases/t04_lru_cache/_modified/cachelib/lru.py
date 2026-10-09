import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._ttl = ttl
        self._clock = clock
        self._data = OrderedDict()  # key -> (value, expires_at or None)
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def _expired(self, entry):
        expires_at = entry[1]
        return expires_at is not None and self._clock() >= expires_at

    def get(self, key, default=None):
        entry = self._data.get(key)
        if entry is None:
            self._misses += 1
            return default
        if self._expired(entry):
            del self._data[key]
            self._misses += 1
            self._expirations += 1
            return default
        self._data.move_to_end(key)
        self._hits += 1
        return entry[0]

    def put(self, key, value):
        expires_at = None if self._ttl is None else self._clock() + self._ttl
        self._data[key] = (value, expires_at)
        self._data.move_to_end(key)
        if len(self._data) > self._capacity:
            self._data.popitem(last=False)
            self._evictions += 1

    def delete(self, key):
        return self._data.pop(key, None) is not None

    def stats(self):
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "expirations": self._expirations,
        }

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        entry = self._data.get(key)
        if entry is None:
            return False
        if self._expired(entry):
            del self._data[key]
            self._expirations += 1
            return False
        return True
