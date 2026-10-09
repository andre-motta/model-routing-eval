import threading

from metrics import Counter


def test_no_lost_updates():
    c = Counter()

    def work():
        for _ in range(2000):
            c.incr("hits")

    ts = [threading.Thread(target=work) for _ in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert c.get("hits") == 16000
