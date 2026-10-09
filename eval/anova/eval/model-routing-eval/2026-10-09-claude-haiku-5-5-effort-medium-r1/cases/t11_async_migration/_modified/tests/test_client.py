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


def test_non_transient_error_is_not_retried():
    calls = {"n": 0}

    async def broken(url):
        calls["n"] += 1
        raise ValueError("boom")

    async def run():
        c = Client(transport=broken, retries=3)
        res = await c.get_many(["u"])
        assert isinstance(res[0], FetchError) and isinstance(res[0].cause, ValueError)

    asyncio.run(run())
    assert calls["n"] == 1


def test_get_many_keeps_input_order_when_completion_differs():
    delays = {"slow": 0.05, "fast": 0.0}

    async def transport(url):
        await asyncio.sleep(delays[url])
        return url.encode()

    async def run():
        return await Client(transport=transport).get_many(["slow", "fast"])

    assert asyncio.run(run()) == [b"slow", b"fast"]


def test_get_many_respects_max_concurrency():
    state = {"in_flight": 0, "peak": 0}

    async def transport(url):
        state["in_flight"] += 1
        state["peak"] = max(state["peak"], state["in_flight"])
        await asyncio.sleep(0.01)
        state["in_flight"] -= 1
        return b"ok"

    async def run():
        urls = [f"u{i}" for i in range(20)]
        return await Client(transport=transport, max_concurrency=3).get_many(urls)

    res = asyncio.run(run())
    assert len(res) == 20 and all(r == b"ok" for r in res)
    assert state["peak"] == 3


def test_summarize():
    async def run():
        return await aggregate.summarize(Client(), ["http://x/1", "http://x/404"])

    assert asyncio.run(run()) == {
        "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}


def test_fetch_all_sync_wrapper():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)


def test_fetch_all_with_injected_transport():
    async def transport(url):
        return url.encode()

    assert fetch_all(["a", "b"], transport=transport) == [b"a", b"b"]
