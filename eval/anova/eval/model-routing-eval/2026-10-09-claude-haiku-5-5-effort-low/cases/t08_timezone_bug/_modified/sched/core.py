from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    zone = ZoneInfo(tz)
    # Take the date in the target zone, not UTC: 23:30 UTC is already the next day in Berlin.
    local_today = now.astimezone(zone).date()
    candidate = datetime.combine(local_today, time(hour, minute), tzinfo=zone)
    if candidate <= now:
        # Step the calendar date, not 24h of elapsed time: across DST the wall-clock
        # time would otherwise drift by an hour.
        candidate = datetime.combine(local_today + timedelta(days=1), time(hour, minute), tzinfo=zone)
    return candidate
