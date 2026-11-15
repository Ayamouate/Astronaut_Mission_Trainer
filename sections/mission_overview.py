"""Landing dashboard for the signed-in astronaut."""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape

import streamlit as st

from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_readiness_cards
from components.status_indicators import render_alert
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from state import initialize_state


def _elapsed_time(history) -> str:
    if "event_type" in history:
        history = history[history["event_type"] != "exercise"]
    if history.empty or "timestamp" not in history:
        return "Awaiting first check-in"
    timestamps = history["timestamp"].dropna()
    if timestamps.empty:
        return "Awaiting first check-in"
    elapsed = timestamps.max() - timestamps.min()
    return f"{max(elapsed.days, 0):02d} days"


def render() -> None:
    """Render the high-signal mission landing page."""
    initialize_state()
    profile = escape(str(st.session_state.get("astronaut_email", "")))
    results = st.session_state["last_results"]
    history = st.session_state["history"]
    score = readiness_score(results)
    state = readiness_state(score, results)
    last_sync = datetime.now(timezone.utc).strftime("%H:%M UTC")

    render_section_header("Mission Overview", SECTION_SUBTITLES["Mission Overview"], state)
    st.markdown(
        f'<div class="mission-overview-strip"><div><span class="strip-label">MISSION PROFILE</span><strong>ASTROCARE / CREW HEALTH</strong><small>Signed in as {profile}</small></div>'
        f'<div><span class="strip-label">ELAPSED HEALTH LOG</span><strong>{_elapsed_time(history)}</strong><small>Last sync Â· {last_sync}</small></div>'
        f'<div><span class="strip-label">OPERATING MODE</span><strong>SELF-ASSESSMENT</strong><small>Human review remains in the loop</small></div></div>',
        unsafe_allow_html=True,
    )
    render_alert(state)
    render_readiness_cards(score, state, results, st.session_state["checkins"], history)

    render_section_bar("Core health snapshot", "latest evaluated readings")
    render_indicator_cards(results, ["heart_rate", "systolic_bp", "spo2", "body_temp", "sleep_duration", "hydration_score"], INDICATORS, columns=3, history=history)

    render_section_bar("Recent health trend", "context for human review")
    render_history_chart(history, "heart_rate", INDICATORS, "Cardiovascular load Â· last 14 mission days")
