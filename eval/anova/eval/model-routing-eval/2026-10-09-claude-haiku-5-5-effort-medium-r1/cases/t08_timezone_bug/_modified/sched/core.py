from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_run(now: datetime, hour: int, minute: int, tz: str) -> datetime:
    """Next hour:minute in tz strictly after now. `now` may be naive (treated as UTC) or aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    # Normalize to UTC so the comparison below is between instants, not wall-clock fields
    now = now.astimezone(timezone.utc)
    zone = ZoneInfo(tz)
    # "Today" is the calendar date in the target zone, not in UTC
    local_today = now.astimezone(zone).date()
    # Step through local calendar days (not 24h blocks) so DST changes keep the wall-clock time
    candidate = datetime(local_today.year, local_today.month, local_today.day, hour, minute, tzinfo=zone)
    if candidate > now:
        return candidate
    tomorrow = local_today + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, tzinfo=zone)
