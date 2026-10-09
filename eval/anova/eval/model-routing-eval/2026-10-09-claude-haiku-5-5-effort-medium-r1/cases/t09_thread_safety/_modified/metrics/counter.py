import contextlib
import threading
import time


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so updates to different counters do not
    serialise each other. ``_guard`` protects the dicts themselves and is only
    held for short, non-blocking sections. Lock order is always name lock
    first, then ``_guard``, so the two can never deadlock.
    """

    def __init__(self):
        self._guard = threading.Lock()
        self._values = {}
        self._locks = {}

    def _lock_for(self, name):
        with self._guard:
            lock = self._locks.get(name)
            if lock is None:
                lock = self._locks[name] = threading.Lock()
            return lock

    def incr(self, name, by=1):
        with self._lock_for(name):
            current = self._values.get(name, 0)
            time.sleep(0)  # yield, simulates real work between read and write
            with self._guard:
                self._values[name] = current + by

    def get(self, name):
        with self._guard:
            return self._values.get(name, 0)

    def snapshot(self):
        with self._guard:
            return dict(self._values)

    def reset(self, name=None):
        if name is None:
            # Take every per-name lock in a fixed order so no in-flight incr
            # can write a stale value back after the clear.
            with self._guard:
                names = sorted(self._locks)
                locks = [self._locks[n] for n in names]
            with contextlib.ExitStack() as stack:
                for lock in locks:
                    stack.enter_context(lock)
                with self._guard:
                    self._values.clear()
        else:
            with self._lock_for(name), self._guard:
                self._values.pop(name, None)
