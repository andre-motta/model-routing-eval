import asyncio

import pytest

from fetcher import Client, FetchError, TransientError, aggregate
from fetcher.sync import fetch_all


async def _get_and_many():
    async with Client() as c:
        assert await c.get("http://x/1") == b"payload for http://x/1"
        res = await c.get_many(["http://x/1", "http://x/404"])
        assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)


def test_get_and_many():
    asyncio.run(_get_and_many())


async def _retry_then_succeed():
    attempts = {"n": 0}

    async def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("try again")
        return b"ok"

    c = Client(transport=flaky, retries=3)
    assert await c.get("u") == b"ok" and c.calls == 3


def test_retry_then_succeed():
    asyncio.run(_retry_then_succeed())


async def _retries_exhausted():
    async def always_transient(url):
        raise TransientError("down")

    c = Client(transport=always_transient, retries=3)
    with pytest.raises(TransientError):
        await c.get("u")
    assert c.calls == 3


def test_retries_exhausted():
    asyncio.run(_retries_exhausted())


async def _non_transient_not_retried():
    async def broken(url):
        raise ValueError("bad")

    c = Client(transport=broken, retries=3)
    res = await c.get_many(["u"])
    assert c.calls == 1
    assert isinstance(res[0], FetchError) and isinstance(res[0].cause, ValueError)


def test_non_transient_not_retried():
    asyncio.run(_non_transient_not_retried())


async def _limits_concurrency_and_keeps_order():
    in_flight = 0
    peak = 0

    async def slow(url):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return url.encode()

    urls = [f"u{i}" for i in range(6)]
    c = Client(transport=slow, max_concurrency=2)
    res = await c.get_many(urls)
    assert res == [u.encode() for u in urls]
    assert peak == 2


def test_get_many_limits_concurrency_and_keeps_order():
    asyncio.run(_limits_concurrency_and_keeps_order())


def test_max_concurrency_must_be_positive():
    with pytest.raises(ValueError):
        Client(max_concurrency=0)


async def _close_blocks_get():
    c = Client()
    await c.close()
    with pytest.raises(RuntimeError):
        await c.get("http://x/1")


def test_close_blocks_get():
    asyncio.run(_close_blocks_get())


async def _summarize():
    c = Client()
    assert await aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
        "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}


def test_summarize():
    asyncio.run(_summarize())


def test_fetch_all_sync_wrapper():
    async def fake(url):
        return url.encode()

    assert fetch_all(["a", "b"], transport=fake) == [b"a", b"b"]


def test_fetch_all_default_transport():
    res = fetch_all(["http://x/1", "http://x/404"])
    assert res[0] == b"payload for http://x/1" and isinstance(res[1], FetchError)
