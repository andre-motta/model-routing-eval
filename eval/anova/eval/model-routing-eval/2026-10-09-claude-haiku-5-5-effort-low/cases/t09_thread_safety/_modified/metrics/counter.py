import threading


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so increments to different counters do not
    contend with each other. ``_registry_lock`` guards the lock table and
    adds/removes keys in ``_values``, and is held while copying it.
    """

    def __init__(self):
        self._values = {}
        self._locks = {}
        self._registry_lock = threading.Lock()

    def _lock_for(self, name):
        lock = self._locks.get(name)
        if lock is None:
            with self._registry_lock:
                lock = self._locks.setdefault(name, threading.Lock())
        return lock

    def incr(self, name, by=1):
        with self._lock_for(name):
            self._values[name] = self._values.get(name, 0) + by

    def get(self, name):
        # A single dict read is atomic, and writers only ever store whole values.
        return self._values.get(name, 0)

    def snapshot(self):
        with self._registry_lock:
            return dict(self._values)

    def reset(self, name=None):
        if name is None:
            with self._registry_lock:
                names = list(self._values)
            for n in names:
                self.reset(n)
            return
        with self._lock_for(name):
            self._values.pop(name, None)
