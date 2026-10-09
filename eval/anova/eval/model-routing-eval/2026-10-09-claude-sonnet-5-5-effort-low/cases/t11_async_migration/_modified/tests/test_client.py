import asyncio

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


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


def test_retry_exhausted_only_transient():
    async def always(url):
        raise TransientError("x")

    async def bad(url):
        raise ValueError("x")

    async def run():
        c = Client(transport=always, retries=2)
        res = await c.get_many(["u"])
        assert isinstance(res[0], FetchError) and c.calls == 2
        c = Client(transport=bad, retries=3)
        await c.get_many(["u"])
        assert c.calls == 1

    asyncio.run(run())


def test_concurrency_limit_and_order():
    state = {"cur": 0, "max": 0}

    async def slow(url):
        state["cur"] += 1
        state["max"] = max(state["max"], state["cur"])
        await asyncio.sleep(0.01)
        state["cur"] -= 1
        return url.encode()

    async def run():
        urls = [f"u{i}" for i in range(12)]
        res = await Client(slow, max_concurrency=3).get_many(urls)
        assert res == [u.encode() for u in urls]
        assert state["max"] == 3

    asyncio.run(run())


def test_summarize():
    async def run():
        c = Client()
        assert await aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
            "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}

    asyncio.run(run())


def test_sync_wrapper():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)
