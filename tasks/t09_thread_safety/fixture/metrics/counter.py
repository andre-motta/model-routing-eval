import time


class Counter:
    """Named counters. Intended to be shared across request-handler threads."""

    def __init__(self):
        self._values = {}

    def incr(self, name, by=1):
        current = self._values.get(name, 0)
        time.sleep(0)  # yield, simulates real work between read and write
        self._values[name] = current + by

    def get(self, name):
        return self._values.get(name, 0)

    def snapshot(self):
        return dict(self._values)

    def reset(self, name=None):
        if name is None:
            self._values.clear()
        else:
            self._values.pop(name, None)
