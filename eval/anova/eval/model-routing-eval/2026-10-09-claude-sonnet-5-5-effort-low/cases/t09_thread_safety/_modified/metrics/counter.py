import threading
import time


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so unrelated counters do not contend. A short
    registry lock guards the structure of the dicts (adding/removing keys) and
    is only ever taken while holding at most one name lock (order: name lock,
    then registry lock), which rules out deadlocks.
    """

    def __init__(self):
        self._values = {}
        self._name_locks = {}
        self._registry = threading.Lock()

    def _lock_for(self, name):
        with self._registry:
            lock = self._name_locks.get(name)
            if lock is None:
                lock = self._name_locks[name] = threading.Lock()
            return lock

    def incr(self, name, by=1):
        with self._lock_for(name):
            current = self._values.get(name, 0)
            time.sleep(0)  # yield, simulates real work between read and write
            with self._registry:
                self._values[name] = current + by

    def get(self, name):
        with self._registry:
            return self._values.get(name, 0)

    def snapshot(self):
        with self._registry:
            return dict(self._values)

    def reset(self, name=None):
        if name is None:
            with self._registry:
                names = list(self._name_locks)
            for n in names:
                self.reset(n)
            return
        with self._lock_for(name):
            with self._registry:
                self._values.pop(name, None)
