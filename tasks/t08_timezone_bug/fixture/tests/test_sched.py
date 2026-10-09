from datetime import datetime, timezone

from sched import next_run


def test_result_is_after_now_late_evening_utc():
    now = datetime(2026, 6, 1, 23, 30, tzinfo=timezone.utc)   # already 01:30 on June 2 in Berlin
    nxt = next_run(now, 1, 0, "Europe/Berlin")
    assert nxt > now
    assert (nxt.year, nxt.month, nxt.day, nxt.hour) == (2026, 6, 3, 1)
