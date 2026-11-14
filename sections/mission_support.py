"""Mission Support section: action guidance, alerts, readiness, and escalation context."""

from __future__ import annotations

import streamlit as st

from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_readiness_cards, render_summary_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from gamification import badges_for_checkins, current_streak, points_for_results
from state import initialize_state


def _guidance_for(status: str) -> tuple[str, str]:
    return {
        "normal": ("NORMAL MONITORING", "Continue the planned schedule and record context with the next reading."),
        "attention": ("WARNING · REVIEW", "Repeat the signal using the approved method and contact the appropriate support path if it persists."),
        "critical": ("CRITICAL · ACT NOW", "Stop the relevant task, follow the approved mission procedure, and contact crew medical / operations support immediately."),
        "unknown": ("NO READING", "Collect a reading when the approved device and mission schedule allow."),
    }.get(status, ("STATUS UNAVAILABLE", "Use the mission medical plan for the next action."))


def render() -> None:
    """Render the Mission Support dashboard."""
    initialize_state()
    results = st.session_state["last_results"]
    history = st.session_state["history"]
    score = readiness_score(results)
    state = readiness_state(score, results)
    checkins = st.session_state["checkins"]

    render_section_header("Mission Support", SECTION_SUBTITLES["Mission Support"], state)
    render_alert(state)
    render_readiness_cards(score, state, results, checkins)

    render_section_bar("Mission health alerts", "ordered by urgency · simulated data")
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_signal_rows(sort_results(results), limit=8)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">How to read status <span>HUMAN IN THE LOOP</span></div>', unsafe_allow_html=True)
        for status, title in [("normal", "Normal monitoring"), ("attention", "Warning requiring attention"), ("critical", "Critical: immediate action")]:
            label, detail = _guidance_for(status)
            st.markdown(f'<div class="guidance-row"><span class="status-dot {status}"></span><div><strong>{title}</strong><p>{detail}</p></div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Approved next actions", "decision support, not a diagnosis")
    prioritized = sort_results(results)
    actions = [item for item in prioritized if item.get("status") in {"attention", "critical"}]
    if not actions:
        actions = prioritized[:3]
    for index, result in enumerate(actions[:5], start=1):
        label, detail = _guidance_for(result.get("status", "unknown"))
        st.markdown(f'<div class="action-card"><div class="step">{index:02d}</div><div><strong>{result.get("label", "Signal")}</strong><span class="action-status {result.get("status", "unknown")}">{label}</span><p>{result.get("action", detail)}</p></div></div>', unsafe_allow_html=True)

    render_section_bar("Medical link and equipment readiness", "operational checklist")
    render_summary_cards([
        {"label": "Medical link", "value": "READY", "detail": "crew medical / flight surgeon path", "tone": "good"},
        {"label": "Approved devices", "value": "READY", "detail": "verify device quality before repeat", "tone": "good"},
        {"label": "Emergency mode", "value": "STANDBY", "detail": "follow vehicle procedure if alarmed", "tone": "warn"},
    ], columns=3)

    render_section_bar("Mission health history", "trend context for the next human review")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "heart_rate", INDICATORS, "Cardiovascular history")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "radiation_dose", INDICATORS, "Radiation context")
        st.markdown("</div>", unsafe_allow_html=True)

    points = points_for_results(results)
    streak = current_streak(checkins)
    badges = badges_for_checkins(checkins, streak, score)
    render_section_bar("Crew reinforcement", "consistency protects the baseline")
    left, right = st.columns([.8, 1.2], gap="large")
    with left:
        render_summary_cards([
            {"label": "Points today", "value": str(points), "detail": "+10 for a normal evaluated signal", "tone": "good"},
            {"label": "Check-in streak", "value": f"{streak} days", "detail": "keep the rhythm", "tone": "good"},
        ], columns=2)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Earned on this mission <span>REINFORCEMENT</span></div>', unsafe_allow_html=True)
        for badge in badges:
            color = "#83f2ce" if badge["earned"] else "#516579"
            earned = "earned" if badge["earned"] else "locked"
            st.markdown(f'<div class="signal-row"><div style="font-size:1.15rem;color:{color};width:25px;text-align:center">{badge["icon"]}</div><div class="signal-main"><div class="signal-label">{badge["name"]}</div><div class="signal-message">{badge["detail"]}</div></div><div class="status-text" style="color:{color}">{earned}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="info-panel"><div class="panel-title">Safety boundary <span>IMPORTANT</span></div><p>AstroCare is an explainable prototype using simulated readings and illustrative thresholds. It does not diagnose conditions or replace NASA / agency procedures, a mission medical operations plan, behavioral-health support, operations control, or flight-surgeon judgment.</p></div>', unsafe_allow_html=True)

