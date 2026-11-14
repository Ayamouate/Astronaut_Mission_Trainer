"""Physical Wellness section: exercise, strength, recovery, and countermeasures."""

from __future__ import annotations

import streamlit as st

from components.charts import render_bar_chart, render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_summary_cards
from components.status_indicators import render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state, trend_for
from state import initialize_state


PHYSICAL_INDICATORS = ["exercise_minutes", "grip_strength_pct", "heart_rate", "sleep_duration", "hydration_score"]


def _selected_results(results: list[dict], ids: list[str]) -> list[dict]:
    return [result for result in results if result.get("id") in ids]


def render() -> None:
    """Render the Physical Wellness dashboard."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    physical_results = _selected_results(results, PHYSICAL_INDICATORS)
    score = readiness_score(physical_results)
    state = readiness_state(score, physical_results)

    render_section_header("Physical Wellness", SECTION_SUBTITLES["Physical Wellness"], state)
    render_indicator_cards(results, PHYSICAL_INDICATORS, INDICATORS, columns=3)
    render_summary_cards([
        {"label": "Bone health", "value": "N/A", "detail": "No validated bone telemetry in demo data", "tone": "muted"},
    ], columns=1)

    recent_minutes = 0.0
    if "exercise_minutes" in history.columns:
        recent_minutes = float(history["exercise_minutes"].tail(7).sum())
    weekly_target = 420.0  # Demonstration schedule target; not a universal clinical limit.
    progress = min(max(recent_minutes / weekly_target, 0.0), 1.0)
    render_section_bar("Countermeasure progress", "last 7 mission days · illustrative schedule")
    left, right = st.columns([1.25, .75], gap="large")
    with left:
        st.markdown('<div class="panel progress-panel"><div class="panel-title">Exercise completion <span>WEEKLY VIEW</span></div>', unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f'<div class="progress-readout"><strong>{recent_minutes:.0f} min</strong><span>of {weekly_target:.0f} illustrative minutes logged</span></div>', unsafe_allow_html=True)
        st.caption("The displayed target is a prototype planning aid. Mission-prescribed exercise plans and medical guidance take priority.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        current = next((item for item in physical_results if item.get("id") == "exercise_minutes"), None)
        tone = "good" if current and current.get("status") == "normal" else "warn" if current and current.get("status") == "attention" else "bad"
        render_summary_cards([{"label": "Today’s exercise", "value": "—" if not current or current.get("value") is None else f'{current["value"]:g} min', "detail": current.get("status_label", "No reading") if current else "No reading", "tone": tone}], columns=1)

    render_section_bar("Activity and recovery history", "use trends to discuss the plan with the crew medical team")
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_bar_chart(history, "exercise_minutes", INDICATORS, "Exercise minutes")
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "grip_strength_pct", INDICATORS, "Strength vs. personal baseline", color="#F4BC62")
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Signals to discuss", "priority-ordered guidance")
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_signal_rows(sort_results(physical_results))
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Recovery readout <span>CONTEXT</span></div>', unsafe_allow_html=True)
        for indicator_id in ["sleep_duration", "hydration_score", "grip_strength_pct"]:
            indicator = INDICATORS[indicator_id]
            trend = trend_for(history, indicator_id)
            st.markdown(f'<div class="signal-row"><div class="signal-main"><div class="signal-label">{indicator["short_label"]}</div><div class="signal-message">{indicator["why_exam"]}</div></div><div class="status-text">{trend["label"]}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="info-panel"><div class="panel-title">Why microgravity matters <span>SPACE PHYSIOLOGY</span></div><p>Reduced mechanical loading can contribute to muscle and bone changes, while fluid redistribution and workload affect cardiovascular conditioning. Approved aerobic and resistive exercise, adequate recovery, and trend review are countermeasures—not a substitute for the mission medical plan.</p></div>', unsafe_allow_html=True)

