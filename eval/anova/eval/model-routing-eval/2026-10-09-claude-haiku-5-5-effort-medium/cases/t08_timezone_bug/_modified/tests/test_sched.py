from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sched import next_run


def test_result_is_after_now_late_evening_utc():
    now = datetime(2026, 6, 1, 23, 30, tzinfo=timezone.utc)   # already 01:30 on June 2 in Berlin
    nxt = next_run(now, 1, 0, "Europe/Berlin")
    assert nxt > now
    assert (nxt.year, nxt.month, nxt.day, nxt.hour) == (2026, 6, 3, 1)


def test_next_day_keeps_wall_clock_across_dst_change():
    now = datetime(2026, 3, 28, 12, 0, tzinfo=timezone.utc)   # 13:00 CET on March 28
    nxt = next_run(now, 9, 0, "Europe/Berlin")                 # DST starts March 29
    assert nxt == datetime(2026, 3, 29, 9, 0, tzinfo=ZoneInfo("Europe/Berlin"))
