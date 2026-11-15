"""Shared Streamlit session-state lifecycle for the modular frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from config import INDICATORS, SAMPLE_HISTORY_PATH
from engine import append_check_in, evaluate_measurements
from auth import get_checkins, save_checkin as persist_checkin


def _empty_history() -> pd.DataFrame:
    """Return a schema-compatible empty history when demo data is unavailable."""
    columns = ["timestamp", *INDICATORS]
    return pd.DataFrame({"timestamp": pd.Series(dtype="datetime64[ns]"), **{column: pd.Series(dtype="float64") for column in columns[1:]}})


def _load_history() -> pd.DataFrame:
    """Load the simulated mission history without failing the dashboard on missing data."""
    try:
        history = pd.read_csv(SAMPLE_HISTORY_PATH, parse_dates=["timestamp"])
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        return _empty_history()

    if "timestamp" not in history.columns:
        history.insert(0, "timestamp", pd.NaT)
    return history


def _latest_measurements(history: pd.DataFrame) -> dict[str, float]:
    """Build the current measurement mapping from the latest available row."""
    if history.empty:
        return {}
    latest = history.iloc[-1]
    measurements: dict[str, float] = {}
    for indicator_id in INDICATORS:
        value = latest.get(indicator_id)
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
            st.session_state["history"]["timestamp"] = pd.to_datetime(st.session_state["history"]["timestamp"])
        st.session_state["measurement_values"] = _latest_measurements(st.session_state["history"])
        st.session_state["last_results"] = evaluate_measurements(st.session_state["measurement_values"], INDICATORS)
        st.session_state["checkins"] = len(st.session_state["history"])
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
        st.session_state["checkins"] = len(st.session_state["history"])
    if "sleep_quality" not in st.session_state:
        st.session_state["sleep_quality"] = 4


def current_results() -> list[dict[str, Any]]:
    """Return the most recent evaluated indicators."""
    initialize_state()
    return st.session_state["last_results"]


def save_check_in(values: dict[str, Any], timestamp: datetime | str) -> None:
    """Merge a partial check-in, evaluate it, and append it to mission history."""
    initialize_state()
    merged = dict(st.session_state["measurement_values"])
    merged.update({key: value for key, value in values.items() if key in INDICATORS})
    st.session_state["measurement_values"] = merged
    st.session_state["last_results"] = evaluate_measurements(merged, INDICATORS)
    timestamp_value = timestamp if isinstance(timestamp, str) else timestamp.strftime("%Y-%m-%d %H:%M")
    st.session_state["history"] = append_check_in(st.session_state["history"], merged, timestamp_value)
    st.session_state["checkins"] += 1
    if st.session_state.get("astronaut_email"):
        persist_checkin(st.session_state["astronaut_email"], {"timestamp": timestamp_value, **merged})

