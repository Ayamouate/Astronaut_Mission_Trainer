"""Health Monitoring section: physiology, readiness, and the full check-in."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from components.body_map import render_body_map
from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_readiness_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from state import initialize_state, save_check_in


HEALTH_INDICATORS = ["heart_rate", "systolic_bp", "spo2", "body_temp", "sleep_duration", "hydration_score"]
CATEGORY_ORDER = ["Health Monitoring", "Physical Wellness", "Mental Wellness", "Space Environment"]


def _input_value(indicator: dict, current: dict[str, float]) -> float:
    value = current.get(indicator["id"], indicator["default"])
    return min(max(float(value), float(indicator["min"])), float(indicator["max"]))


def _render_input(indicator: dict, current: dict[str, float], key_prefix: str) -> float:
    """Render one configured measurement input with its safe bounds."""
    return st.number_input(
        indicator["label"],
        min_value=float(indicator["min"]),
        max_value=float(indicator["max"]),
        value=_input_value(indicator, current),
        step=float(indicator["step"]),
        key=f"{key_prefix}_{indicator['id']}",
        help=f"Measure in space: {indicator['measure_in_space']}",
    )


def _render_check_in() -> None:
    """Render the original complete self-assessment without coupling it to other pages."""
    current = st.session_state["measurement_values"]
    with st.form("mission_checkin"):
        tabs = st.tabs(["Vitals", "Physical", "Mental", "Environment"])
        values: dict[str, float] = {}
        for tab, category in zip(tabs, CATEGORY_ORDER):
            with tab:
                descriptions = {
                    "Health Monitoring": "Core physiological signals",
                    "Physical Wellness": "Recovery and countermeasures",
                    "Mental Wellness": "Private performance and mood check",
                    "Space Environment": "The habitat is part of the patient",
                }
                st.caption(descriptions[category])
                category_items = [item for item in INDICATORS.values() if item.get("category") == category]
                columns = st.columns(2)
                for index, indicator in enumerate(category_items):
                    with columns[index % 2]:
                        values[indicator["id"]] = _render_input(indicator, current, "full_checkin")
        submitted = st.form_submit_button("Save check-in and evaluate", use_container_width=True)
    if submitted:
        save_check_in(values, datetime.now(timezone.utc))
        st.success("Check-in saved. Review the guidance below before resuming safety-critical work.")


def render() -> None:
    """Render the Health Monitoring dashboard."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    score = readiness_score(results)
    state = readiness_state(score, results)

    render_section_header("Health Monitoring", SECTION_SUBTITLES["Health Monitoring"], state)
    render_alert(state)
    render_readiness_cards(score, state, results, st.session_state["checkins"])

    render_section_bar("Core physiological signals", "latest evaluated check-in")
    render_indicator_cards(results, HEALTH_INDICATORS, INDICATORS, columns=3)

    render_section_bar("Crew health map", "select a system to inspect the signal")
    left, right = st.columns([1.05, 1.45], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">Body systems <span>LIVE</span></div>', unsafe_allow_html=True)
        render_body_map(results, INDICATORS)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Priority signals <span>latest check-in</span></div>', unsafe_allow_html=True)
        render_signal_rows(sort_results(results), limit=7)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Baseline trend", "last 14 mission days")
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "heart_rate", INDICATORS, "Cardiovascular load")
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "sleep_duration", INDICATORS, "Recovery window")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Open full check-in", expanded=False):
        st.markdown('<div class="section-note form-note">Use approved devices and mission procedures. Symptoms and flight-surgeon direction take priority over any dashboard range.</div>', unsafe_allow_html=True)
        _render_check_in()

