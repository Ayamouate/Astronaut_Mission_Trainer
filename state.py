"""Shared Streamlit session-state lifecycle for the modular frontend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from config import INDICATORS, SAMPLE_HISTORY_PATH
from engine import append_check_in, evaluate_measurements
from auth import get_checkins, save_checkin as persist_checkin


def _empty_history() -> pd.DataFrame:
    """Return a schema-compatible empty history when demo data is unavailable."""
    columns = ["timestamp", *INDICATORS, "event_type"]
    return pd.DataFrame({"timestamp": pd.Series(dtype="datetime64[ns, UTC]"), **{column: pd.Series(dtype="float64") for column in INDICATORS}, "event_type": pd.Series(dtype="object")})


def _load_history() -> pd.DataFrame:
    """Load the simulated mission history without failing the dashboard on missing data."""
    try:
        history = pd.read_csv(SAMPLE_HISTORY_PATH, parse_dates=["timestamp"])
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        return _empty_history()

    if "timestamp" not in history.columns:
        history.insert(0, "timestamp", pd.NaT)
    history["timestamp"] = pd.to_datetime(history["timestamp"], utc=True, errors="coerce")
    if "event_type" not in history.columns:
        history["event_type"] = "health"
    return history


def _latest_measurements(history: pd.DataFrame) -> dict[str, float]:
    """Build the current measurement mapping from the latest available row."""
    if history.empty:
        return {}
    measurements: dict[str, float] = {}
    for indicator_id in INDICATORS:
        if indicator_id not in history:
            continue
        available = pd.to_numeric(history[indicator_id], errors="coerce").dropna()
        value = available.iloc[-1] if not available.empty else None
        if value is not None and not pd.isna(value):
            measurements[indicator_id] = float(value)
    return measurements


def initialize_state() -> None:
    """Initialize only the shared state required by all dashboard sections."""
    email = st.session_state.get("astronaut_email")
    if st.session_state.get("state_astronaut") != email:
        entries = get_checkins(email) if email else []
        st.session_state["history"] = pd.DataFrame(entries) if entries else _empty_history()
        if not st.session_state["history"].empty:
            st.session_state["history"]["timestamp"] = pd.to_datetime(st.session_state["history"]["timestamp"], utc=True, errors="coerce")
            if "event_type" not in st.session_state["history"]:
                st.session_state["history"]["event_type"] = "health"
        st.session_state["measurement_values"] = _latest_measurements(st.session_state["history"])
        st.session_state["last_results"] = evaluate_measurements(st.session_state["measurement_values"], INDICATORS)
        history = st.session_state["history"]
        st.session_state["checkins"] = int((history.get("event_type", pd.Series("health", index=history.index)) != "exercise").sum())
        st.session_state["state_astronaut"] = email
        st.session_state["selected_system"] = "Cardiovascular"
        st.session_state["sleep_quality"] = 4
        return

    if "history" not in st.session_state:
        st.session_state["history"] = _load_history()

    if "measurement_values" not in st.session_state:
        # Migrate the earlier key if a running Streamlit session still has it.
        legacy_values = st.session_state["values"] if "values" in st.session_state else None
        st.session_state["measurement_values"] = legacy_values if isinstance(legacy_values, dict) else _latest_measurements(st.session_state["history"])

    if "last_results" not in st.session_state:
        st.session_state["last_results"] = evaluate_measurements(st.session_state["measurement_values"], INDICATORS)
    if "selected_system" not in st.session_state:
        st.session_state["selected_system"] = "Cardiovascular"
    if "checkins" not in st.session_state:
        history = st.session_state["history"]
        st.session_state["checkins"] = int((history.get("event_type", pd.Series("health", index=history.index)) != "exercise").sum())
    if "sleep_quality" not in st.session_state:
        st.session_state["sleep_quality"] = 4


def current_results() -> list[dict[str, Any]]:
    """Return the most recent evaluated indicators."""
    initialize_state()
    return st.session_state["last_results"]


def save_check_in(values: dict[str, Any], timestamp: datetime | str, event_type: str = "health") -> None:
    """Merge a partial check-in, evaluate it, and append it to mission history."""
    initialize_state()
    merged = dict(st.session_state["measurement_values"])
    merged.update({key: value for key, value in values.items() if key in INDICATORS})
    st.session_state["measurement_values"] = merged
    st.session_state["last_results"] = evaluate_measurements(merged, INDICATORS)
    timestamp_value = pd.Timestamp(timestamp)
    timestamp_value = timestamp_value.tz_localize("UTC") if timestamp_value.tzinfo is None else timestamp_value.tz_convert("UTC")
    timestamp_value = timestamp_value.isoformat()
    submitted = {key: value for key, value in values.items() if key in INDICATORS}
    st.session_state["history"] = append_check_in(st.session_state["history"], submitted, timestamp_value, event_type)
    if event_type != "exercise":
        st.session_state["checkins"] += 1
    if st.session_state.get("astronaut_email"):
        persist_checkin(st.session_state["astronaut_email"], {"timestamp": timestamp_value, **submitted, "event_type": event_type})

