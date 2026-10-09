import time
from collections import OrderedDict


class LRUCache:
    """Least-recently-used cache with optional per-entry TTL.

    Entries are stored in an OrderedDict ordered from least to most recently
    used. Each value is kept as a (value, expires_at) pair, where expires_at is
    None when the cache has no TTL.
    """

    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._ttl = ttl
        self._clock = clock
        self._data = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def _is_expired(self, expires_at):
        return expires_at is not None and self._clock() >= expires_at

    def get(self, key, default=None):
        entry = self._data.get(key)
        if entry is None:
            self._misses += 1
            return default
        value, expires_at = entry
        if self._is_expired(expires_at):
            del self._data[key]
            self._expirations += 1
            self._misses += 1
            return default
        self._data.move_to_end(key)
        self._hits += 1
        return value

    def put(self, key, value):
        expires_at = None if self._ttl is None else self._clock() + self._ttl
        self._data[key] = (value, expires_at)
        self._data.move_to_end(key)
        if len(self._data) > self._capacity:
            _, (_, lru_expires_at) = self._data.popitem(last=False)
            if self._is_expired(lru_expires_at):
                self._expirations += 1
            else:
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
        self._purge_expired()
        return len(self._data)

    def __contains__(self, key):
        entry = self._data.get(key)
        if entry is None:
            return False
        if self._is_expired(entry[1]):
            del self._data[key]
            self._expirations += 1
            return False
        return True

    def _purge_expired(self):
        expired = [key for key, (_, expires_at) in self._data.items()
                   if self._is_expired(expires_at)]
        for key in expired:
            del self._data[key]
        self._expirations += len(expired)
