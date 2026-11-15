"""Mental Wellness section: private self-report, recovery, and cognition signals."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from components.charts import render_history_chart, render_multi_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_summary_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, SECTION_SUBTITLES
from engine import readiness_score, readiness_state
from state import initialize_state, save_check_in


MENTAL_INDICATORS = ["mood_score", "stress_score", "sleep_duration", "reaction_time_ms"]


def _value(results: list[dict], indicator_id: str, default: float) -> float:
    item = next((result for result in results if result.get("id") == indicator_id), None)
    return default if not item or item.get("value") is None else float(item["value"])


def _mood_label(value: int) -> str:
    return {1: "1 · struggling", 2: "2 · low", 3: "3 · steady", 4: "4 · good", 5: "5 · thriving"}.get(value, str(value))


def _render_private_check_in(results: list[dict]) -> None:
    """Collect a minimal self-report while keeping free text out of mission history."""
    current_mood = int(_value(results, "mood_score", 4))
    current_stress = int(_value(results, "stress_score", 2))
    current_sleep = _value(results, "sleep_duration", 7.5)
    with st.form("mental_wellbeing_checkin"):
        mood = st.select_slider("Mood selection", options=[1, 2, 3, 4, 5], value=min(max(current_mood, 1), 5), format_func=_mood_label)
        stress = st.slider("Stress level", min_value=1, max_value=5, value=min(max(current_stress, 1), 5), help="A private self-report; 5 means the highest perceived stress.")
        sleep_quality = st.slider("Sleep quality", min_value=1, max_value=5, value=int(st.session_state.get("sleep_quality", 4)), help="This demo rating is held in session state and is not written to the CSV history.")
        sleep_duration = st.number_input("Sleep duration in the last 24 h", min_value=0.0, max_value=14.0, value=min(max(float(current_sleep), 0.0), 14.0), step=0.5)
        wellbeing_note = st.text_area("Optional private reflection", placeholder="Do not include urgent symptoms here; use the approved crew support channel.", help="This prototype does not save free-text reflections to mission history.")
        submitted = st.form_submit_button("Save private check-in", use_container_width=True)
    if submitted:
        save_check_in({"mood_score": mood, "stress_score": stress, "sleep_duration": sleep_duration}, datetime.now(timezone.utc))
        st.session_state["sleep_quality"] = sleep_quality
        # Keep the variable intentionally local: the note is not saved or displayed later.
        del wellbeing_note
        st.success("Self-report saved. The optional reflection was not written to mission history.")


def render() -> None:
    """Render the Mental Wellness dashboard."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    mental_results = [result for result in results if result.get("id") in MENTAL_INDICATORS]
    score = readiness_score(mental_results)
    state = readiness_state(score, mental_results)

    render_section_header("Mental Wellness", SECTION_SUBTITLES["Mental Wellness"], state)
    render_alert(state)
    render_indicator_cards(results, MENTAL_INDICATORS, INDICATORS, columns=4, history=history)
    render_summary_cards([
        {"label": "Fatigue level", "value": "N/A", "detail": "Use sleep and reaction-time trends as context", "tone": "muted"},
        {"label": "Social connection", "value": "N/A", "detail": "No direct isolation telemetry in demo data", "tone": "muted"},
    ], columns=2)

    st.markdown('<div class="privacy-note"><strong>Private by design:</strong> mood and stress are self-reported signals, not diagnoses. Use approved behavioral-health support for sensitive concerns; urgent safety concerns should be shared with the crew immediately. This prototype does not store free-text reflections in the mission CSV.</div>', unsafe_allow_html=True)

    render_section_bar("Wellbeing trends", "recent self-report and performance signals")
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_multi_history_chart(history, ["mood_score", "stress_score"], INDICATORS, "Mood and stress trend")
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_history_chart(history, "sleep_duration", INDICATORS, "Sleep window")
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_bar("Recommended recovery actions", "supportive prompts, not clinical diagnoses")
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_signal_rows(sort_results(mental_results))
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Crew-friendly reset <span>LOW RISK</span></div><div class="playbook-item"><div class="step">01</div><div><strong>Protect the next recovery window</strong><p>Reduce nonessential workload and keep the approved sleep/light routine consistent.</p></div></div><div class="playbook-item"><div class="step">02</div><div><strong>Reconnect with the crew</strong><p>Use a trusted crew member or scheduled behavioral-health check-in when isolation or stress persists.</p></div></div><div class="playbook-item"><div class="step">03</div><div><strong>Repeat under consistent conditions</strong><p>Compare trends at a similar time, posture, device, and workload context.</p></div></div></div>', unsafe_allow_html=True)

    with st.expander("Open private wellbeing check-in", expanded=False):
        _render_private_check_in(results)

