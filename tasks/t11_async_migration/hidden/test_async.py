import asyncio
import inspect
import time

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


def run(coro):
    return asyncio.run(coro)


def test_async_api_shape():
    assert inspect.iscoroutinefunction(Client.get)
    assert inspect.iscoroutinefunction(Client.get_many)
    assert inspect.iscoroutinefunction(Client.close)
    assert inspect.iscoroutinefunction(aggregate.summarize)
    assert hasattr(Client, "__aenter__") and hasattr(Client, "__aexit__")


def test_get_and_many_order_and_errors():
    async def go():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404", "http://x/2"])
            assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)
            assert res[2] == b"payload for http://x/2" and res[1].url == "http://x/404"
    run(go())


def test_concurrency_limit_and_actual_concurrency():
    active = {"now": 0, "max": 0}

    async def slow(url):
        active["now"] += 1
        active["max"] = max(active["max"], active["now"])
        await asyncio.sleep(0.05)
        active["now"] -= 1
        return b"x"

    async def go(limit):
        c = Client(transport=slow, max_concurrency=limit)
        t0 = time.perf_counter()
        res = await c.get_many([f"u{i}" for i in range(10)])
        return time.perf_counter() - t0, res

    elapsed, res = run(go(5))
    assert len(res) == 10 and active["max"] == 5
    assert elapsed < 0.3, "requests were not run concurrently"
    active["max"] = 0
    run(go(2))
    assert active["max"] == 2


def test_retry_policy():
    attempts = {"n": 0}

    async def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("again")
        return b"ok"

    async def go():
        c = Client(transport=flaky, retries=3, backoff=0.001)
        assert await c.get("u") == b"ok" and c.calls == 3
        attempts["n"] = -10
        c2 = Client(transport=flaky, retries=2, backoff=0.001)
        try:
            await c2.get("u")
        except TransientError:
            pass
        else:
            raise AssertionError("should raise after retries exhausted")
    run(go())


def test_summarize_and_sync_wrapper():
    async def go():
        c = Client()
        return await aggregate.summarize(c, ["http://x/1", "http://x/404"])
    assert run(go()) == {"ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)


def test_no_blocking_sleep_left():
    import fetcher.client as m
    src = inspect.getsource(m)
    assert "time.sleep" not in src
