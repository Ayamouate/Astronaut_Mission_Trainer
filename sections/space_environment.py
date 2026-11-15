"""Space Environment section: habitat telemetry, radiation, and operational context."""

from __future__ import annotations

import streamlit as st

from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards
from components.status_indicators import render_alert
from config import INDICATORS, SECTION_SUBTITLES
from engine import evaluate_measurements, readiness_score, readiness_state
from state import initialize_state


ENVIRONMENT_INDICATORS = ["cabin_co2", "radiation_dose"]
SIMULATED_ENVIRONMENT = {"cabin_co2": 2200.0, "radiation_dose": 0.8}


def _sparkline(color: str) -> str:
    """Return a small decorative trend line for simulated telemetry."""
    return (
        f'<svg class="telemetry-sparkline" viewBox="0 0 120 24" aria-hidden="true">'
        f'<path d="M1 17 L12 14 L23 16 L34 9 L45 12 L56 7 L67 11 L78 6 L89 9 L100 4 L119 7" '
        f'style="stroke:{color}"/></svg>'
    )


def _render_simulated_cards() -> None:
    """Render non-persistent demo telemetry with a live-monitoring treatment."""
    cards = [
        ("Cabin CO₂", "2200 ppm", "NOMINAL · simulated", "#36D6E7"),
        ("Radiation dose", "0.8 mSv", "NOMINAL · simulated", "#4D8DFF"),
    ]
    columns = st.columns(2)
    for column, (label, value, detail, color) in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="telemetry-card"><div class="telemetry-card-head"><span class="telemetry-label"><span class="pulse-dot" style="--pulse-color:{color}"></span>{label}</span><span class="telemetry-mode">SIM</span></div>'
                f'<div class="telemetry-value">{value}</div><div class="telemetry-detail" style="color:{color}">{detail}</div>{_sparkline(color)}</div>',
                unsafe_allow_html=True,
            )


def render() -> None:
    """Render the Space Environment dashboard using only available telemetry."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    environment_results = [result for result in results if result.get("id") in ENVIRONMENT_INDICATORS]
    simulate = st.toggle("Simulated telemetry", value=True, help="Use demonstration values without writing them to your astronaut history.")
    if simulate:
        environment_results = evaluate_measurements(SIMULATED_ENVIRONMENT, INDICATORS)
    score = readiness_score(environment_results)
    state = readiness_state(score, environment_results)

    render_section_header("Space Environment", SECTION_SUBTITLES["Space Environment"], state)
    render_alert(state)
    if simulate:
        _render_simulated_cards()
    else:
        render_indicator_cards(results, ENVIRONMENT_INDICATORS, INDICATORS, columns=2, history=history)

    render_section_bar("Telemetry coverage", "vehicle integration status")
    st.markdown(
        '<div class="coverage-banner"><span class="coverage-icon">◌</span><div><strong>5 vehicle sensors awaiting integration</strong><p>Temperature, humidity, pressure, oxygen, and microgravity exposure are intentionally hidden until validated telemetry is available.</p></div><span class="coverage-status">NOT CONNECTED</span></div>',
        unsafe_allow_html=True,
    )

    render_section_bar("Environmental history", "normal bands are configured in the indicator library")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="panel-title">Cabin CO₂ trend <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_history_chart(history, "cabin_co2", INDICATORS, "", color="#36D6E7")
    with right:
        st.markdown('<div class="panel-title">Radiation dose · last 24 h <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_history_chart(history, "radiation_dose", INDICATORS, "", color="#4D8DFF")

    st.markdown('<div class="info-panel"><div class="panel-title">Why the habitat matters <span>HUMAN–SYSTEM LINK</span></div><p>Closed-habitat air quality can affect cognition and performance, while ionizing radiation is cumulative and may be episodic. Environmental alerts should be handled through vehicle alarms, approved radiation procedures, operations support, and the crew medical plan—not improvised treatment.</p></div>', unsafe_allow_html=True)
