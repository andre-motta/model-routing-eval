import asyncio

from .client import Client


def fetch_all(urls, transport=None):
    async def run():
        async with Client(transport) as client:
            return await client.get_many(urls)

    return asyncio.run(run())
