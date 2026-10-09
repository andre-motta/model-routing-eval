import asyncio

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


def test_get_and_many():
    async def main():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404"])
            assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)
        assert c.closed

    asyncio.run(main())


def test_retry_then_succeed():
    attempts = {"n": 0}

    async def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("try again")
        return b"ok"

    async def main():
        c = Client(flaky, retries=3)
        assert await c.get("u") == b"ok" and c.calls == 3

    asyncio.run(main())


def test_retry_exhausted_and_non_transient_not_retried():
    async def always(url):
        raise TransientError("no")

    async def bad(url):
        raise ValueError("bad")

    async def main():
        c = Client(always, retries=2)
        res = await c.get_many(["a"])
        assert isinstance(res[0], FetchError) and c.calls == 2
        c = Client(bad, retries=3)
        res = await c.get_many(["a"])
        assert isinstance(res[0], FetchError) and c.calls == 1

    asyncio.run(main())


def test_get_many_order_and_concurrency_limit():
    running = {"now": 0, "max": 0}

    async def slow(url):
        running["now"] += 1
        running["max"] = max(running["max"], running["now"])
        await asyncio.sleep(0.01 * (5 - int(url)))
        running["now"] -= 1
        return url.encode()

    async def main():
        c = Client(slow, max_concurrency=2)
        urls = [str(i) for i in range(5)]
        assert await c.get_many(urls) == [u.encode() for u in urls]
        assert running["max"] == 2

    asyncio.run(main())


def test_closed_client():
    async def main():
        c = Client()
        await c.close()
        res = await c.get_many(["a"])
        assert isinstance(res[0], FetchError)

    asyncio.run(main())


def test_summarize():
    async def main():
        c = Client()
        assert await aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
            "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}

    asyncio.run(main())


def test_sync_fetch_all():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)

    async def t(url):
        return b"custom"

    assert fetch_all(["a"], transport=t) == [b"custom"]
