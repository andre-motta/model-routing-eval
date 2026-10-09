import asyncio

from . import aggregate
from .client import Client


async def _fetch_all(urls, transport):
    async with Client(transport) as client:
        return await client.get_many(urls)


def fetch_all(urls, transport=None):
    return asyncio.run(_fetch_all(list(urls), transport))
