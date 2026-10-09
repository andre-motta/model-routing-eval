import asyncio
import time

from fetcher import Client, FetchError, TransientError, aggregate, sync


def test_get_and_many():
    async def run():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404"])
            assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)

    asyncio.run(run())


def test_retry_then_succeed():
    attempts = {"n": 0}

    async def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("try again")
        return b"ok"

    async def run():
        c = Client(transport=flaky, retries=3)
        assert await c.get("u") == b"ok" and c.calls == 3

    asyncio.run(run())


def test_non_transient_error_not_retried():
    calls = {"n": 0}

    async def broken(url):
        calls["n"] += 1
        raise ValueError("boom")

    async def run():
        c = Client(transport=broken, retries=3)
        res = await c.get_many(["u"])
        assert isinstance(res[0], FetchError) and calls["n"] == 1

    asyncio.run(run())


def test_get_many_keeps_order_and_limits_concurrency():
    state = {"active": 0, "peak": 0}

    async def slow(url):
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        await asyncio.sleep(0.01)
        state["active"] -= 1
        return url.encode()

    urls = [f"http://x/{i}" for i in range(20)]

    async def run():
        c = Client(transport=slow, max_concurrency=4)
        res = await c.get_many(urls)
        assert res == [u.encode() for u in urls]

    asyncio.run(run())
    assert state["peak"] <= 4


def test_get_many_runs_concurrently():
    async def slow(url):
        await asyncio.sleep(0.05)
        return b"ok"

    async def run():
        c = Client(transport=slow, max_concurrency=10)
        start = time.perf_counter()
        await c.get_many([f"u{i}" for i in range(10)])
        return time.perf_counter() - start

    assert asyncio.run(run()) < 0.3


def test_closed_client_raises():
    async def run():
        c = Client()
        await c.close()
        try:
            await c.get("http://x/1")
        except RuntimeError:
            return
        raise AssertionError("expected RuntimeError")

    asyncio.run(run())


def test_summarize():
    async def run():
        c = Client()
        return await aggregate.summarize(c, ["http://x/1", "http://x/404"])

    assert asyncio.run(run()) == {
        "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}


def test_sync_fetch_all():
    res = sync.fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)
