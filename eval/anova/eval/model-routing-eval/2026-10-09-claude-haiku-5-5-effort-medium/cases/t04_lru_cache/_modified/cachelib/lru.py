import time
from collections import OrderedDict


class LRUCache:
    # Entries are stored as key -> (value, expires_at); expires_at is None when ttl is None.
    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.ttl = ttl
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
        expires_at = None if self.ttl is None else self._clock() + self.ttl
        self._data[key] = (value, expires_at)
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            _, (_, lru_expires_at) = self._data.popitem(last=False)
            # An expired entry leaving the cache is an expiration, not an eviction.
            if self._is_expired(lru_expires_at):
                self._expirations += 1
            else:
                self._evictions += 1

    def delete(self, key):
        entry = self._data.pop(key, None)
        if entry is None:
            return False
        if self._is_expired(entry[1]):
            self._expirations += 1
            return False
        return True

    def stats(self):
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "expirations": self._expirations,
        }

    # Expired entries not yet touched are still counted here; purging them would be O(n).
    def __len__(self):
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
