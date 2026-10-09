import asyncio

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


def run(coro):
    return asyncio.run(coro)


def test_get_and_many():
    async def main():
        async with Client() as c:
            assert await c.get("http://x/1") == b"payload for http://x/1"
            res = await c.get_many(["http://x/1", "http://x/404"])
            assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)

    run(main())


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

    run(main())


def test_get_many_keeps_order_and_limits_concurrency():
    in_flight = {"now": 0, "peak": 0}

    async def slow(url):
        in_flight["now"] += 1
        in_flight["peak"] = max(in_flight["peak"], in_flight["now"])
        await asyncio.sleep(0.01)
        in_flight["now"] -= 1
        return url.encode()

    urls = [f"u{i}" for i in range(12)]

    async def main():
        c = Client(transport=slow, max_concurrency=3)
        return await c.get_many(urls)

    res = run(main())
    assert res == [u.encode() for u in urls]
    assert in_flight["peak"] == 3


def test_summarize():
    async def main():
        c = Client()
        return await aggregate.summarize(c, ["http://x/1", "http://x/404"])

    assert run(main()) == {
        "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}


def test_fetch_all_sync_wrapper():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)


def test_fetch_all_custom_transport():
    async def transport(url):
        return url.encode()

    assert fetch_all(["a", "b"], transport=transport) == [b"a", b"b"]
