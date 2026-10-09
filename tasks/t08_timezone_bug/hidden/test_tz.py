from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sched import next_run

B = "Europe/Berlin"


def test_result_is_after_now_late_evening_utc():
    now = datetime(2026, 6, 1, 23, 30, tzinfo=timezone.utc)
    nxt = next_run(now, 1, 0, B)
    assert nxt > now
    assert (nxt.year, nxt.month, nxt.day, nxt.hour, nxt.minute) == (2026, 6, 3, 1, 0)
    assert nxt.tzinfo is not None and nxt.utcoffset().total_seconds() == 7200


def test_same_local_day_when_still_ahead():
    now = datetime(2026, 6, 1, 22, 30, tzinfo=timezone.utc)   # 00:30 June 2 Berlin
    nxt = next_run(now, 9, 0, B)
    assert (nxt.day, nxt.hour) == (2, 9)


def test_strictly_after():
    now = datetime(2026, 6, 2, 9, 0, tzinfo=ZoneInfo(B))
    assert next_run(now, 9, 0, B).day == 3


def test_dst_spring_forward_keeps_wall_clock():
    # DST starts 2026-03-29 02:00 in Berlin. 09:00 must stay 09:00 local across the change,
    # and the UTC gap between the two runs is 23h, not 24h.
    now = datetime(2026, 3, 28, 10, 0, tzinfo=ZoneInfo(B))
    nxt = next_run(now, 9, 0, B)
    assert (nxt.day, nxt.hour, nxt.utcoffset().total_seconds()) == (29, 9, 7200)
    before = next_run(datetime(2026, 3, 27, 10, 0, tzinfo=ZoneInfo(B)), 9, 0, B)
    assert (nxt.astimezone(timezone.utc) - before.astimezone(timezone.utc)).total_seconds() == 23 * 3600


def test_dst_fall_back_keeps_wall_clock():
    # DST ends 2026-10-25 03:00 in Berlin.
    now = datetime(2026, 10, 24, 10, 0, tzinfo=ZoneInfo(B))
    nxt = next_run(now, 9, 0, B)
    assert (nxt.day, nxt.hour, nxt.utcoffset().total_seconds()) == (25, 9, 3600)


def test_naive_now_is_utc():
    nxt = next_run(datetime(2026, 6, 1, 23, 30), 1, 0, B)
    assert nxt.day == 3
