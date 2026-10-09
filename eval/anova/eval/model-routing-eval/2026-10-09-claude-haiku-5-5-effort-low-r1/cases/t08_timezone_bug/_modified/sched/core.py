from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    # take the calendar date in the target zone, not in UTC
    day = now.astimezone(zone).date()
    while True:
        candidate = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        if candidate > now:
            return candidate
        # step by calendar days, not 24 elapsed hours, so DST changes don't shift the wall-clock time
        day += timedelta(days=1)
