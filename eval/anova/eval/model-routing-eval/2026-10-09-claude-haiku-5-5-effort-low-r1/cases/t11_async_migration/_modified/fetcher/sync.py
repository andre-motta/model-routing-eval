import asyncio

from .client import Client


async def _fetch_all(urls, transport):
    async with Client(transport) as client:
        return await client.get_many(urls)


def fetch_all(urls, transport=None):
    """Blocking wrapper around Client.get_many for non-async callers."""
    return asyncio.run(_fetch_all(urls, transport))
