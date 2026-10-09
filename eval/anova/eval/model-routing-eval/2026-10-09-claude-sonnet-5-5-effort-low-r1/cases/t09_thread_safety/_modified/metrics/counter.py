import threading
import time


class _Cell:
    __slots__ = ("lock", "value")

    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    A registry lock guards only the name -> cell mapping; each counter has its
    own lock, so increments of different names do not contend.
    """

    def __init__(self):
        self._cells = {}
        self._registry_lock = threading.Lock()

    def incr(self, name, by=1):
        with self._registry_lock:
            cell = self._cells.get(name)
            if cell is None:
                cell = self._cells[name] = _Cell()
        with cell.lock:
            current = cell.value
            time.sleep(0)  # yield, simulates real work between read and write
            cell.value = current + by

    def get(self, name):
        with self._registry_lock:
            cell = self._cells.get(name)
        return 0 if cell is None else cell.value

    def snapshot(self):
        with self._registry_lock:
            return {name: cell.value for name, cell in self._cells.items()}

    def reset(self, name=None):
        # Dropping cells (rather than zeroing) keeps snapshot() key semantics.
        # An incr that already holds a dropped cell is ordered before the reset.
        with self._registry_lock:
            if name is None:
                self._cells.clear()
            else:
                self._cells.pop(name, None)
