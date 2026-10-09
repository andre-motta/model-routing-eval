import threading
import time


class _Cell:
    __slots__ = ("lock", "value")

    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0


class Counter:
    """Named counters. Intended to be shared across request-handler threads.

    Each name has its own lock, so increments to different counters do not
    contend. A registry lock guards only the name -> cell mapping. Lock order
    is always registry lock, then cell locks; incr() never holds both.
    """

    def __init__(self):
        self._cells = {}
        self._registry_lock = threading.Lock()

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
        if cell is None:
            return 0
        with cell.lock:
            return cell.value

    def snapshot(self):
        # Point-in-time copy: hold every cell lock so no increment is mid-flight.
        with self._registry_lock:
            cells = list(self._cells.items())
            for _, cell in cells:
                cell.lock.acquire()
            try:
                return {name: cell.value for name, cell in cells}
            finally:
                for _, cell in cells:
                    cell.lock.release()

    def reset(self, name=None):
        with self._registry_lock:
            if name is None:
                self._cells.clear()
            else:
                self._cells.pop(name, None)
