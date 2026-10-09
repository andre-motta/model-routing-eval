from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    today = now.date()
    candidate = datetime(today.year, today.month, today.day, hour, minute, tzinfo=zone)
    if candidate <= now:
        # advance one day; do the arithmetic in UTC to avoid tz surprises
        candidate = (candidate.astimezone(timezone.utc) + timedelta(days=1)).astimezone(zone)
    return candidate
