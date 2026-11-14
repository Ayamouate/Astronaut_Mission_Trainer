"""Space Environment section: habitat telemetry, radiation, and operational context."""

from __future__ import annotations

import streamlit as st

from components.charts import render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_summary_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from state import initialize_state


ENVIRONMENT_INDICATORS = ["cabin_co2", "radiation_dose"]
UNAVAILABLE_TELEMETRY = [
    ("Cabin temperature", "Not in demo telemetry"),
    ("Cabin humidity", "Not in demo telemetry"),
    ("Cabin pressure", "Not in demo telemetry"),
    ("Cabin oxygen", "Not in demo telemetry"),
    ("Microgravity exposure", "Not in demo telemetry"),
]


def render() -> None:
    """Render the Space Environment dashboard using only available telemetry."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    environment_results = [result for result in results if result.get("id") in ENVIRONMENT_INDICATORS]
    score = readiness_score(environment_results)
    state = readiness_state(score, environment_results)

    render_section_header("Space Environment", SECTION_SUBTITLES["Space Environment"], state)
    render_alert(state)
    render_indicator_cards(results, ENVIRONMENT_INDICATORS, INDICATORS, columns=2)

    render_section_bar("Telemetry coverage", "the demo shows only fields present in the supplied mission log")
    render_summary_cards([{"label": label, "value": "N/A", "detail": detail, "tone": "muted"} for label, detail in UNAVAILABLE_TELEMETRY], columns=3)
    st.caption("Cabin temperature, humidity, pressure, oxygen, and microgravity exposure require validated vehicle telemetry integrations before they can be displayed here.")

    render_section_bar("Environmental history", "normal bands are configured in the indicator library")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "cabin_co2", INDICATORS, "Cabin CO₂", color="#42D9E8")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "radiation_dose", INDICATORS, "Radiation dose · last 24 h", color="#F4BC62")
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Environmental notifications", "operations context matters")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    render_signal_rows(sort_results(environment_results))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="info-panel"><div class="panel-title">Why the habitat matters <span>HUMAN–SYSTEM LINK</span></div><p>Closed-habitat air quality can affect cognition and performance, while ionizing radiation is cumulative and may be episodic. Environmental alerts should be handled through vehicle alarms, approved radiation procedures, operations support, and the crew medical plan—not improvised treatment.</p></div>', unsafe_allow_html=True)

