"""Calendar-day streak calculations for health and exercise activity."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable


def current_streak(timestamps: Iterable[Any]) -> int:
    """Count consecutive UTC calendar days with at least one recorded event."""
    days: set[date] = set()
    for timestamp in timestamps:
        if isinstance(timestamp, datetime):
            normalized = timestamp.astimezone(timezone.utc) if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
            days.add(normalized.date())
        elif isinstance(timestamp, date):
            days.add(timestamp)
        elif timestamp:
            try:
                parsed = datetime.fromisoformat(str(timestamp))
                normalized = parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                days.add(normalized.date())
            except ValueError:
                continue
    today = datetime.now(timezone.utc).date()
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
