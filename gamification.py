"""Small, mission-friendly reinforcement layer for recurring self-checks."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable


def points_for_results(results: list[dict[str, Any]]) -> int:
    points = {"normal": 10, "attention": 6, "critical": 2, "unknown": 0}
    return sum(points.get(result["status"], 0) for result in results)


def badges_for_checkins(checkin_count: int, streak: int, score: int) -> list[dict[str, str]]:
    return [
        {"name": "Baseline", "detail": "First complete health check", "icon": "◉", "earned": checkin_count >= 1},
        {"name": "Steady orbit", "detail": "Three check-ins logged", "icon": "✦", "earned": checkin_count >= 3},
        {"name": "Mission rhythm", "detail": "A 5-day check-in streak", "icon": "↗", "earned": streak >= 5},
        {"name": "Crew ready", "detail": "Readiness stays above 85", "icon": "✓", "earned": score >= 85},
    ]


def current_streak(checkin_timestamps: Iterable[Any]) -> int:
    """Count consecutive calendar days with at least one check-in, once per day."""
    days: set[date] = set()
    for timestamp in checkin_timestamps:
        if isinstance(timestamp, datetime):
            days.add(timestamp.date())
        elif isinstance(timestamp, date):
            days.add(timestamp)
        elif timestamp:
            try:
                days.add(datetime.fromisoformat(str(timestamp)).date())
            except ValueError:
                continue
    today = date.today()
    # A streak remains active through today even if today's check-in is still pending.
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak

