Migrate the `fetcher` package from blocking I/O to asyncio while keeping behaviour:

- `fetcher.Client` becomes an async client: `async get(url)`, `async get_many(urls)`,
  `async with` support, and `close()` becomes `async close()`.
- Transport is injected: `Client(transport)` where `transport` is an async callable
  `async (url) -> bytes`. The default transport uses `asyncio.sleep` to simulate latency
  as the sync one uses `time.sleep`.
- `get_many` runs requests concurrently with a concurrency limit `max_concurrency`
  (constructor arg, default 5). Results keep input order. Errors for individual URLs
  are returned as `FetchError` instances in the result list, not raised.
- Retries: same policy as today (up to `retries` attempts, exponential backoff using
  `asyncio.sleep`), retry only on `TransientError`.
- `aggregate.summarize(client, urls)` becomes `async` and keeps its return shape.
- Keep a thin sync wrapper `fetcher.sync.fetch_all(urls, transport=None)` that runs the
  async code with `asyncio.run` for callers that are not async.

Port the existing tests to pytest-asyncio or plain `asyncio.run`, keep them passing, and
run them.
