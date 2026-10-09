from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    day = now.astimezone(zone).date()  # local date, not the UTC date
    while True:
        candidate = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        # Round-trip through UTC so a wall time skipped by a DST gap lands on a real instant.
        candidate = candidate.astimezone(timezone.utc).astimezone(zone)
        if candidate > now:
            return candidate
        day += timedelta(days=1)  # advance the local calendar day, keeping wall-clock time
