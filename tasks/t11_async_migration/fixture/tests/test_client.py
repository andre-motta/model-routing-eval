from fetcher import Client, FetchError, TransientError, aggregate


def test_get_and_many():
    with Client() as c:
        assert c.get("http://x/1") == b"payload for http://x/1"
        res = c.get_many(["http://x/1", "http://x/404"])
        assert res[0].startswith(b"payload") and isinstance(res[1], FetchError)


def test_retry_then_succeed():
    attempts = {"n": 0}

    def flaky(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("try again")
        return b"ok"

    c = Client(transport=flaky, retries=3)
    assert c.get("u") == b"ok" and c.calls == 3


def test_summarize():
    c = Client()
    assert aggregate.summarize(c, ["http://x/1", "http://x/404"]) == {
        "ok": 1, "failed": ["http://x/404"], "bytes": len(b"payload for http://x/1")}
