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


@st.dialog("Health Monitoring", width="large")
def _show_health_evaluation(results: list[dict]) -> None:
    """Show the latest check-in results in a focused health-monitoring pop-up."""
    st.markdown("### Core physiological signals")
    st.caption("Latest evaluated check-in · Watch and Escalate labels flag readings for review.")
    render_signal_rows(sort_results(results))


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


def _render_check_in() -> bool:
    """Render every check-in category together and return whether it was evaluated."""
    current = st.session_state["measurement_values"]
    with st.form("mission_checkin"):
        values: dict[str, float] = {}
        sections = {
            "Health Monitoring": ("Vitals", "Core physiological signals"),
            "Physical Wellness": ("Physical", "Recovery and countermeasures"),
            "Mental Wellness": ("Mental", "Mood, stress, sleep, and cognition"),
            "Space Environment": ("Environment", "Habitat conditions"),
        }
        for category in CATEGORY_ORDER:
            title, description = sections[category]
            st.markdown(f"#### {title}")
            st.caption(description)
            category_items = [item for item in INDICATORS.values() if item.get("category") == category]
            columns = st.columns(2)
            for index, indicator in enumerate(category_items):
                with columns[index % 2]:
                    values[indicator["id"]] = _render_input(indicator, current, "full_checkin")
        submitted = st.form_submit_button("Evaluate my health", type="primary", use_container_width=True)
    if submitted:
        save_check_in(values, datetime.now(timezone.utc))
    return submitted


def render() -> None:
    """Render the Health Monitoring dashboard."""
    initialize_state()
    with st.expander("Open full check-in", expanded=True):
        st.markdown('<div class="section-note form-note">Use approved devices and mission procedures. Symptoms and flight-surgeon direction take priority over any dashboard range.</div>', unsafe_allow_html=True)
        evaluated = _render_check_in()

    # Read after form submission so the evaluation shown on this same page is current.
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    score = readiness_score(results)
    state = readiness_state(score, results)
    if evaluated:
        _show_health_evaluation(results)

    render_section_header("Health Monitoring", SECTION_SUBTITLES["Health Monitoring"], state)
    render_alert(state)
    render_readiness_cards(score, state, results, st.session_state["checkins"], history)

    render_section_bar("Core physiological signals", "latest evaluated check-in")
    render_indicator_cards(results, HEALTH_INDICATORS, INDICATORS, columns=3, history=history)

    render_section_bar("Crew health map", "select a system to inspect its readings")
    render_body_map(results, INDICATORS)
    st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Baseline trend", "last 14 mission days")
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        render_history_chart(history, "heart_rate", INDICATORS, "Cardiovascular load")
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        render_history_chart(history, "sleep_duration", INDICATORS, "Recovery window")
        st.markdown("</div>", unsafe_allow_html=True)


