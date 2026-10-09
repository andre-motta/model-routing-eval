import contextlib
import threading
import time


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so unrelated counters do not contend. A small
    registry lock guards only the creation of per-name locks. Operations that
    span every counter (snapshot, reset all) take the registry lock and then
    every per-name lock, which yields a consistent point-in-time view. Writers
    never hold a name lock while waiting for the registry lock, so this cannot
    deadlock.
    """

    def __init__(self):
        self._values = {}
        self._locks = {}
        self._registry = threading.Lock()

    def _lock_for(self, name):
        lock = self._locks.get(name)
        if lock is None:
            with self._registry:
                lock = self._locks.setdefault(name, threading.Lock())
        return lock

    @contextlib.contextmanager
    def _all_locked(self):
        with self._registry:
            locks = list(self._locks.values())
            with contextlib.ExitStack() as stack:
                for lock in locks:
                    stack.enter_context(lock)
                yield

    def incr(self, name, by=1):
        with self._lock_for(name):
            current = self._values.get(name, 0)
            time.sleep(0)  # yield, simulates real work between read and write
            self._values[name] = current + by

    def get(self, name):
        with self._lock_for(name):
            return self._values.get(name, 0)

    def snapshot(self):
        with self._all_locked():
            return dict(self._values)

    def reset(self, name=None):
        if name is None:
            with self._all_locked():
                self._values.clear()
        else:
            with self._lock_for(name):
                self._values.pop(name, None)
