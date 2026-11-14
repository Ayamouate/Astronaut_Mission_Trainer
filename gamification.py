"""Small, mission-friendly reinforcement layer for recurring self-checks."""

from __future__ import annotations

from typing import Any


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


def current_streak(checkin_count: int) -> int:
    return min(checkin_count, 7)

