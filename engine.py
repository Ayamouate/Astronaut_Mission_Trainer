"""Decision-support logic for the AstroCare mission health dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


STATUS_ORDER = {"critical": 0, "attention": 1, "normal": 2, "unknown": 3}
STATUS_LABELS = {"normal": "Within range", "attention": "Watch", "critical": "Escalate", "unknown": "No reading"}


def load_indicators(path: str | Path) -> dict[str, dict[str, Any]]:
    import json
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return {item["id"]: item for item in raw["indicators"]}


def _in_range(value: float, boundaries: list[float] | None) -> bool:
    return boundaries is not None and len(boundaries) == 2 and boundaries[0] <= value <= boundaries[1]


def evaluate_indicator(indicator: dict[str, Any], value: float | int | None) -> dict[str, Any]:
    """Return a safe, explainable status for one measurement."""
    if value is None or pd.isna(value):
        return {"id": indicator["id"], "label": indicator["label"], "value": None, "status": "unknown", "status_label": STATUS_LABELS["unknown"], "unit": indicator.get("unit", ""), "action": "Collect a reading when the approved device and mission schedule allow.", "message": "No reading recorded."}
    numeric_value = float(value)
    thresholds = indicator["thresholds"]
    if _in_range(numeric_value, thresholds.get("normal")):
        status = "normal"
    elif _in_range(numeric_value, thresholds.get("attention")):
        status = "attention"
    else:
        status = "critical"
    actions = indicator.get("actions", {})
    return {"id": indicator["id"], "label": indicator["label"], "value": numeric_value, "status": status, "status_label": STATUS_LABELS[status], "unit": indicator.get("unit", ""), "action": actions.get(status, actions.get("attention", "Follow the approved mission protocol.")), "message": indicator.get("status_messages", {}).get(status, "Review the reading with the crew medical officer.")}


def evaluate_measurements(values: dict[str, Any], indicators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [evaluate_indicator(indicator, values[indicator_id]) for indicator_id, indicator in indicators.items() if indicator_id in values]


def readiness_score(results: list[dict[str, Any]]) -> int:
    observed = [result for result in results if result["status"] != "unknown"]
    if not observed:
        return 0
    points = {"normal": 100, "attention": 68, "critical": 25}
    return round(sum(points[item["status"]] for item in observed) / len(observed))


def readiness_state(score: int, results: list[dict[str, Any]]) -> str:
    if any(item["status"] == "critical" for item in results):
        return "ESCALATE"
    if any(item["status"] == "attention" for item in results) or score < 80:
        return "WATCH"
    return "NOMINAL"


def sort_by_priority(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(results, key=lambda item: STATUS_ORDER.get(item["status"], 3))


def trend_for(history: pd.DataFrame, indicator_id: str, window: int = 5) -> dict[str, Any]:
    if indicator_id not in history.columns:
        return {"direction": "flat", "delta": 0.0, "label": "No trend"}
    series = pd.to_numeric(history[indicator_id], errors="coerce").dropna().tail(window)
    if len(series) < 2:
        return {"direction": "flat", "delta": 0.0, "label": "Building baseline"}
    delta = float(series.iloc[-1] - series.iloc[0])
    tolerance = max(abs(float(series.mean())) * 0.015, 0.01)
    if delta > tolerance:
        direction, label = "up", "Rising"
    elif delta < -tolerance:
        direction, label = "down", "Falling"
    else:
        direction, label = "flat", "Stable"
    return {"direction": direction, "delta": delta, "label": label}


def append_check_in(history: pd.DataFrame, values: dict[str, Any], timestamp: str) -> pd.DataFrame:
    row = {column: values.get(column) for column in history.columns if column != "timestamp"}
    row["timestamp"] = timestamp
    updated = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
    updated["timestamp"] = pd.to_datetime(updated["timestamp"])
    return updated.sort_values("timestamp").reset_index(drop=True)

