import asyncio

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


def test_get_and_many():
    async def main():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404"])
            assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)

    asyncio.run(main())


def test_retry_then_succeed():
    attempts = {"n": 0}

    async def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("try again")
        return b"ok"

    async def main():
        c = Client(transport=flaky, retries=3)
        assert await c.get("u") == b"ok" and c.calls == 3

    asyncio.run(main())


def test_summarize():
    async def main():
        c = Client()
        assert await aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
            "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}

    asyncio.run(main())


def test_concurrency_limit_and_order():
    state = {"cur": 0, "max": 0}

    async def slow(url):
        state["cur"] += 1
        state["max"] = max(state["max"], state["cur"])
        await asyncio.sleep(0.01 * (5 - int(url)))
        state["cur"] -= 1
        return url.encode()

    async def main():
        c = Client(transport=slow, max_concurrency=2)
        urls = [str(i) for i in range(5)]
        assert await c.get_many(urls) == [u.encode() for u in urls]

    asyncio.run(main())
    assert state["max"] == 2


def test_no_retry_on_non_transient():
    async def main():
        calls = []

        async def bad(url):
            calls.append(url)
            raise ValueError("x")

        res = await Client(transport=bad).get_many(["u"])
        assert isinstance(res[0], FetchError) and len(calls) == 1

    asyncio.run(main())


def test_sync_wrapper():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)
