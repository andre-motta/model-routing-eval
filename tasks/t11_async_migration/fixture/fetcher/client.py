import time


class FetchError(Exception):
    def __init__(self, url, cause):
        super().__init__(f"{url}: {cause}")
        self.url = url
        self.cause = cause


class TransientError(Exception):
    pass


def default_transport(url):
    time.sleep(0.01)
    if url.endswith("/404"):
        raise KeyError("not found")
    return f"payload for {url}".encode()


class Client:
    def __init__(self, transport=None, retries=3, backoff=0.01):
        self.transport = transport or default_transport
        self.retries = retries
        self.backoff = backoff
        self.closed = False
        self.calls = 0

    def get(self, url):
        if self.closed:
            raise RuntimeError("client closed")
        delay = self.backoff
        for attempt in range(1, self.retries + 1):
            self.calls += 1
            try:
                return self.transport(url)
            except TransientError:
                if attempt == self.retries:
                    raise
                time.sleep(delay)
                delay *= 2

    def get_many(self, urls):
        out = []
        for u in urls:
            try:
                out.append(self.get(u))
            except Exception as e:
                out.append(FetchError(u, e))
        return out

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
