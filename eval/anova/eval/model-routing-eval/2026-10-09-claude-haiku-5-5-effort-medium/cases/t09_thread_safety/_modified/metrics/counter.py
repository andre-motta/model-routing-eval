import threading
import time
from contextlib import ExitStack


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so increments to unrelated counters do not
    contend with each other. ``_table_lock`` only guards the lock table itself.
    Every operation holds at most one counter lock at a time, except
    ``snapshot()``, which takes all of them in sorted name order. That ordering
    is what keeps it deadlock-free.
    """

    def __init__(self):
        self._table_lock = threading.Lock()
        self._locks = {}
        self._values = {}

    def _lock_for(self, name):
        lock = self._locks.get(name)
        if lock is None:
            with self._table_lock:
                lock = self._locks.setdefault(name, threading.Lock())
        return lock

    def incr(self, name, by=1):
        with self._lock_for(name):
            current = self._values.get(name, 0)
            time.sleep(0)  # yield, simulates real work between read and write
            self._values[name] = current + by

    def get(self, name):
        with self._lock_for(name):
            return self._values.get(name, 0)

    def snapshot(self):
        with self._table_lock:
            names = sorted(self._locks)
            locks = [self._locks[name] for name in names]
        with ExitStack() as stack:
            for lock in locks:
                stack.enter_context(lock)
            return dict(self._values)

    def reset(self, name=None):
        if name is None:
            with self._table_lock:
                names = list(self._locks)
            for n in names:
                with self._locks[n]:
                    self._values.pop(n, None)
        else:
            with self._lock_for(name):
                self._values.pop(name, None)
