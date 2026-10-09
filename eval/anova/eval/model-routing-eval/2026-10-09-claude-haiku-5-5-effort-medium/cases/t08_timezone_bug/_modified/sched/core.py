from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    # The calendar date must be taken in the target zone; the UTC date is a day behind
    # for Berlin between 00:00 and 02:00 local time.
    today = now.astimezone(zone).date()
    candidate = datetime(today.year, today.month, today.day, hour, minute, tzinfo=zone)
    if candidate <= now:
        # Step the calendar date rather than adding 24h: a day is 23 or 25 hours across DST changes.
        tomorrow = today + timedelta(days=1)
        candidate = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, tzinfo=zone)
    return candidate
