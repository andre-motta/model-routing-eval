from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    # Work with the local calendar date in the target zone, not the UTC date.
    day = now.astimezone(zone).date()
    while True:
        # Build the candidate from wall-clock fields so DST is applied per day;
        # round-trip through UTC to normalize times that fall in a DST gap.
        candidate = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        candidate = candidate.astimezone(timezone.utc).astimezone(zone)
        if candidate > now:
            return candidate
        day += timedelta(days=1)
