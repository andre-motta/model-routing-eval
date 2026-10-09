import asyncio

from .client import Client


def fetch_all(urls, transport=None):
    """Blocking wrapper around Client.get_many for non-async callers.

    Must not be called from inside a running event loop (asyncio.run restriction).
    """

    async def run():
        async with Client(transport) as c:
            return await c.get_many(urls)

    return asyncio.run(run())
