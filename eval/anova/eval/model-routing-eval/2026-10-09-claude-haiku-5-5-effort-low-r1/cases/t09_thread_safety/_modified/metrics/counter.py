import threading
import time


class _Cell:
    """A single counter value guarded by its own lock."""

    __slots__ = ("lock", "value")

    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so increments to different counters do not
    contend with each other. The registry lock only guards the name-to-cell
    mapping, and is held briefly for lookups, inserts, and removals.
    """

    def __init__(self):
        self._registry_lock = threading.Lock()
        self._cells = {}

    def _cell(self, name):
        with self._registry_lock:
            cell = self._cells.get(name)
            if cell is None:
                cell = self._cells[name] = _Cell()
            return cell

    def incr(self, name, by=1):
        cell = self._cell(name)
        with cell.lock:
            current = cell.value
            time.sleep(0)  # yield, simulates real work between read and write
            cell.value = current + by

    def get(self, name):
        with self._registry_lock:
            cell = self._cells.get(name)
        return cell.value if cell is not None else 0

    def snapshot(self):
        with self._registry_lock:
            return {name: cell.value for name, cell in self._cells.items()}

    def reset(self, name=None):
        with self._registry_lock:
            if name is None:
                self._cells.clear()
            else:
                self._cells.pop(name, None)
