import asyncio

import pytest

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


def test_get_and_many():
    async def run():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404"])
            assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)
        assert c.closed

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


def test_retry_exhausted_raises():
    async def always(url):
        raise TransientError("no")

    async def run():
        c = Client(transport=always, retries=2)
        with pytest.raises(TransientError):
            await c.get("u")
        assert c.calls == 2
        res = await c.get_many(["a"])
        assert isinstance(res[0], FetchError)

    asyncio.run(run())


def test_non_transient_not_retried():
    async def bad(url):
        raise KeyError("x")

    async def run():
        c = Client(transport=bad)
        with pytest.raises(KeyError):
            await c.get("u")
        assert c.calls == 1

    asyncio.run(run())


def test_closed_client_raises():
    async def run():
        c = Client()
        await c.close()
        with pytest.raises(RuntimeError):
            await c.get("u")

    asyncio.run(run())


def test_concurrency_limit_and_order():
    state = {"cur": 0, "max": 0}

    async def slow(url):
        state["cur"] += 1
        state["max"] = max(state["max"], state["cur"])
        await asyncio.sleep(0.01 * (5 - int(url)))
        state["cur"] -= 1
        return url.encode()

    async def run():
        c = Client(transport=slow, max_concurrency=2)
        res = await c.get_many([str(i) for i in range(5)])
        assert res == [str(i).encode() for i in range(5)]
        assert state["max"] == 2

    asyncio.run(run())


def test_summarize():
    async def run():
        c = Client()
        assert await aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
            "ok": 1,
            "failed": ["http://x/404"],
            "bytes": len(b"payload for http://x/1"),
        }

    asyncio.run(run())


def test_sync_wrapper():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)

    async def t(url):
        return b"custom"

    assert fetch_all(["a"], transport=t) == [b"custom"]
