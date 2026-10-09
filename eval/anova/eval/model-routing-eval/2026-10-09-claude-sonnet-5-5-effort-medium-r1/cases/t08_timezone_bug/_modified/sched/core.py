from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    # The calendar day must be the local one in `tz`, not the UTC one.
    day = now.astimezone(zone).date()
    while True:
        # Build the wall time in the zone; a nonexistent time (DST gap) is
        # normalized through UTC so it lands on the first valid instant after the gap.
        wall = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        candidate = wall.astimezone(timezone.utc).astimezone(zone)
        if candidate > now:
            return candidate
        # advance one local calendar day (not 24 elapsed hours, which breaks across DST)
        day += timedelta(days=1)
