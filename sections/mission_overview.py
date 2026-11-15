"""Landing dashboard for the signed-in astronaut."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_readiness_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from state import initialize_state


def _navigate(section: str) -> None:
    """Set the navigation widget before the next script run begins."""
    st.session_state["dashboard_section"] = section


def _elapsed_time(history) -> str:
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
    profile = st.session_state.get("astronaut_email", "")
    results = st.session_state["last_results"]
    history = st.session_state["history"]
    score = readiness_score(results)
    state = readiness_state(score, results)
    last_sync = datetime.now(timezone.utc).strftime("%H:%M UTC")

    render_section_header("Mission Overview", SECTION_SUBTITLES["Mission Overview"], state)
    st.markdown(
        f'<div class="mission-overview-strip"><div><span class="strip-label">MISSION PROFILE</span><strong>ASTROCARE / CREW HEALTH</strong><small>Signed in as {profile}</small></div>'
        f'<div><span class="strip-label">ELAPSED HEALTH LOG</span><strong>{_elapsed_time(history)}</strong><small>Last sync · {last_sync}</small></div>'
        f'<div><span class="strip-label">OPERATING MODE</span><strong>SELF-ASSESSMENT</strong><small>Human review remains in the loop</small></div></div>',
        unsafe_allow_html=True,
    )
    render_alert(state)
    render_readiness_cards(score, state, results, st.session_state["checkins"], history)

    render_section_bar("Priority signals", "ordered by urgency · current check-in")
    left, right = st.columns([1.2, .8], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">What needs attention <span>LIVE REVIEW</span></div>', unsafe_allow_html=True)
        render_signal_rows(sort_results(results), limit=5)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel overview-action-panel"><div class="panel-title">Next best action <span>MISSION GUIDANCE</span></div>', unsafe_allow_html=True)
        priority = next((item for item in sort_results(results) if item.get("status") in {"critical", "attention"}), None)
        if priority:
            st.markdown(f'<div class="action-emphasis"><span class="status-text {priority["status"]}">{priority.get("status_label", "REVIEW")}</span><strong>{priority.get("label", "Signal review")}</strong><p>{priority.get("action", "Follow the approved mission protocol.")}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="action-emphasis nominal"><span class="status-text">NOMINAL</span><strong>Maintain the monitoring cadence</strong><p>Your available signals are inside the illustrative baseline. Complete the next scheduled check-in.</p></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Core health snapshot", "latest evaluated readings")
    render_indicator_cards(results, ["heart_rate", "systolic_bp", "spo2", "body_temp", "sleep_duration", "hydration_score"], INDICATORS, columns=3)

    render_section_bar("Continue your mission workflow", "open a focused workspace")
    quick_sections = [("Health Monitoring", "Vitals, readiness, and full check-in"), ("Physical Wellness", "Exercise and recovery"), ("Mental Wellness", "Private wellbeing check-in"), ("Space Environment", "Cabin and radiation context"), ("Mission Support", "Actions and escalation guidance")]
    columns = st.columns(5)
    for column, (section, detail) in zip(columns, quick_sections):
        with column:
            st.button(
                section,
                key=f"overview_{section}",
                use_container_width=True,
                on_click=_navigate,
                args=(section,),
            )
            st.caption(detail)

    render_section_bar("Recent health trend", "context for human review")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    render_history_chart(history, "heart_rate", INDICATORS, "Cardiovascular load · last 14 mission days")
    st.markdown("</div>", unsafe_allow_html=True)
