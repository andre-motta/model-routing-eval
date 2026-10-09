import asyncio


class FetchError(Exception):
    def __init__(self, url, cause):
        super().__init__(f"{url}: {cause}")
        self.url = url
        self.cause = cause


class TransientError(Exception):
    pass


async def default_transport(url):
    await asyncio.sleep(0.01)
    if url.endswith("/404"):
        raise KeyError("not found")
    return f"payload for {url}".encode()


class Client:
    def __init__(self, transport=None, retries=3, backoff=0.01, max_concurrency=5):
        self.transport = transport or default_transport
        self.retries = retries
        self.backoff = backoff
        self.closed = False
        self.calls = 0
        self.max_concurrency = max_concurrency
        self._sem = asyncio.Semaphore(max_concurrency)

    async def get(self, url):
        if self.closed:
            raise RuntimeError("client closed")
        delay = self.backoff
        for attempt in range(1, self.retries + 1):
            self.calls += 1
            try:
                return await self.transport(url)
            except TransientError:
                if attempt == self.retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    async def _bounded(self, url):
        async with self._sem:
            try:
                return await self.get(url)
            except Exception as e:
                return FetchError(url, e)

    async def get_many(self, urls):
        return list(await asyncio.gather(*(self._bounded(u) for u in urls)))

    async def close(self):
        self.closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
