import inspect
import threading

from metrics import Counter
from metrics import counter as mod


def test_no_lost_updates_many_names():
    c = Counter()

    def work(i):
        for _ in range(1500):
            c.incr("hits"); c.incr(f"worker{i % 3}", 2)

    ts = [threading.Thread(target=work, args=(i,)) for i in range(9)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert c.get("hits") == 13500
    assert sum(c.get(f"worker{k}") for k in range(3)) == 27000


def test_snapshot_is_consistent_copy():
    c = Counter()
    stop = threading.Event()

    def churn():
        while not stop.is_set():
            c.incr("a"); c.incr("b")

    t = threading.Thread(target=churn); t.start()
    try:
        for _ in range(200):
            s = c.snapshot()
            assert isinstance(s, dict)
            s["a"] = -1  # must not affect the counter
            assert c.get("a") >= 0
    finally:
        stop.set(); t.join()


def test_reset_and_api_unchanged():
    c = Counter(); c.incr("x", 5); c.reset("x")
    assert c.get("x") == 0 and c.snapshot() == {}
    c.incr("y"); c.reset(); assert c.snapshot() == {}
    assert set(inspect.signature(Counter.incr).parameters) == {"self", "name", "by"}


def test_uses_a_lock():
    src = inspect.getsource(mod)
    assert "Lock" in src or "RLock" in src
