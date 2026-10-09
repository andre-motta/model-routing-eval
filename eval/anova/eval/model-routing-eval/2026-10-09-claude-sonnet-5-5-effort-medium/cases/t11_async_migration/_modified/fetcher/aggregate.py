from .client import FetchError


async def summarize(client, urls):
    results = await client.get_many(urls)
    ok = [r for r in results if not isinstance(r, FetchError)]
    failed = [r.url for r in results if isinstance(r, FetchError)]
    return {"ok": len(ok), "failed": failed, "bytes": sum(len(r) for r in ok)}
