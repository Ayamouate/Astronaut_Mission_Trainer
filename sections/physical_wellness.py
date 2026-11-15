"""Physical Wellness section: astronaut physical conditioning, training load, musculoskeletal
health, and recovery — built entirely from the crew member's own logged check-ins.

Every number on this page is one of four kinds, and each panel says which:
  MEASURED    — read directly from a logged check-in (data/sample_mission.csv or the crew's own history).
  CALCULATED  — derived transparently from two or more measured values (e.g. a trend direction).
  EDUCATIONAL — general spaceflight-physiology context, not a reading about this astronaut.
No bone density, muscle-mass, or exercise-intensity values are shown because this prototype does
not yet have that telemetry; those gaps are disclosed rather than filled with invented numbers.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from components.charts import render_bar_chart, render_history_chart
from components.header import render_section_bar, render_section_header
from components.metric_cards import render_indicator_cards, render_summary_cards
from components.status_indicators import render_alert, render_signal_rows, sort_results
from config import INDICATORS, ROOT, SECTION_SUBTITLES
from engine import readiness_score, readiness_state, trend_for
from gamification import current_streak
from state import initialize_state, save_check_in


PHYSICAL_INDICATORS = ["exercise_minutes", "grip_strength_pct", "heart_rate", "sleep_duration", "hydration_score"]
RECOVERY_INDICATORS = ["sleep_duration", "hydration_score"]
WEEKLY_TARGET_MIN = 420.0
FREQUENCY_WINDOW = 14
EXERCISE_DEMOS = {
    "Treadmill running (T2)": {
        "focus": "Cardio conditioning",
        "image": ROOT / "assets" / "treadmill_running.png",
    },
    "Resistive squats (ARED)": {
        "focus": "Bone and lower-body strength",
        "image": ROOT / "assets" / "resistive_squats.png",
    },
    "Cycle ergometry (CEVIS)": {
        "focus": "Cardiovascular endurance",
        "image": ROOT / "assets" / "cycle_ergometry.png",
    },
    "Resistive deadlifts": {
        "focus": "Back, glute, and hamstring strength",
        "image": ROOT / "assets" / "resistive_deadlifts.png",
    },
}


def _selected_results(results: list[dict], ids: list[str]) -> list[dict]:
    return [result for result in results if result.get("id") in ids]


def _elapsed_label(history: pd.DataFrame) -> str:
    if history.empty or "timestamp" not in history:
        return "Awaiting first check-in"
    timestamps = history["timestamp"].dropna()
    if timestamps.empty:
        return "Awaiting first check-in"
    elapsed = timestamps.max() - timestamps.min()
    return f"{max(elapsed.days, 0)} days logged"


def _last_assessment_label(history: pd.DataFrame) -> str:
    if history.empty or "timestamp" not in history:
        return "No check-in yet"
    timestamps = history["timestamp"].dropna()
    if timestamps.empty:
        return "No check-in yet"
    return timestamps.max().strftime("%b %d · %H:%M")


def _daily_exercise_totals(history: pd.DataFrame) -> pd.Series:
    """Return the latest logged exercise total for each calendar day."""
    if history.empty or "exercise_minutes" not in history.columns or "timestamp" not in history.columns:
        return pd.Series(dtype="float64")
    frame = history[["timestamp", "exercise_minutes"]].copy()
    if "event_type" in history.columns:
        frame = frame[history["event_type"].eq("exercise") | history["exercise_minutes"].notna()].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame["exercise_minutes"] = pd.to_numeric(frame["exercise_minutes"], errors="coerce").fillna(0)
    frame = frame.dropna(subset=["timestamp"])
    if frame.empty:
        return pd.Series(dtype="float64")
    frame["day"] = frame["timestamp"].dt.floor("D")
    return frame.groupby("day", sort=True)["exercise_minutes"].last()


def _ring_svg(score: int) -> str:
    """A small MEASURED/CALCULATED readiness ring — no decorative fabricated motion."""
    radius = 45
    circumference = 2 * 3.14159265 * radius
    dash = circumference * max(min(score, 100), 0) / 100
    gap = circumference - dash
    value_text = f"{score}" if score else "—"
    return (
        '<div class="pw-ring-wrap"><svg viewBox="0 0 108 108" role="img" aria-label="Physical readiness ring">'
        f'<circle class="pw-ring-track" cx="54" cy="54" r="{radius}"></circle>'
        f'<circle class="pw-ring-value" cx="54" cy="54" r="{radius}" stroke-dasharray="{dash:.1f} {gap:.1f}"></circle>'
        f'</svg><div class="pw-ring-label"><strong>{value_text}</strong><span>Readiness</span></div></div>'
    )


def _training_frequency(history: pd.DataFrame, window: int = FREQUENCY_WINDOW) -> tuple[int, list[bool]]:
    """Count days with a logged exercise minute total above zero — a measured compliance signal."""
    daily_totals = _daily_exercise_totals(history)
    if daily_totals.empty:
        return 0, [False] * window
    today = pd.Timestamp.now(tz="UTC").floor("D")
    days = pd.date_range(end=today, periods=window, freq="D")
    flags = [bool(daily_totals.get(day, 0) > 0) for day in days]
    return sum(flags), flags


def _recovery_balance(history: pd.DataFrame) -> dict[str, str]:
    """A CALCULATED indicator: compares the astronaut's own sleep and exercise trend directions."""
    sleep_trend = trend_for(history, "sleep_duration")
    exercise_trend = trend_for(history, "exercise_minutes")
    if sleep_trend["label"] in {"No trend", "Building baseline"} or exercise_trend["label"] in {"No trend", "Building baseline"}:
        return {"label": "Awaiting baseline", "tone": "muted", "detail": "Log several sleep and exercise check-ins before this comparison can summarize a trend."}
    if sleep_trend["direction"] == "down" and exercise_trend["direction"] == "up":
        return {"label": "Recovery debt risk", "tone": "warn", "detail": "Logged training load is rising while sleep duration is falling. Consider protecting the next rest window before increasing load further."}
    if sleep_trend["direction"] == "up" and exercise_trend["direction"] != "up":
        return {"label": "Recovery trending positive", "tone": "good", "detail": "Sleep duration is improving relative to recent training load — a favorable balance for continued conditioning."}
    return {"label": "Balanced load", "tone": "good", "detail": "No strong divergence between logged training load and sleep trend. Keep the current countermeasure rhythm."}


def _recommendation_cards(physical_results: list[dict]) -> list[tuple[str, str, str]]:
    """Build recommendation cards from the indicator library's own action text — never fabricated."""
    prioritized = sort_results(physical_results)
    actionable = [item for item in prioritized if item.get("status") in {"attention", "critical"}]
    if not actionable:
        actionable = [item for item in prioritized if item.get("status") == "normal"]
    return [(item.get("label", "Signal"), item.get("status", "unknown"), item.get("action") or "Follow the approved mission protocol.") for item in actionable[:3]]


def _render_overview(score: int, state: str, history: pd.DataFrame) -> None:
    st.markdown(
        f'<div class="panel"><div class="pw-overview">{_ring_svg(score)}'
        '<div class="pw-overview-detail"><div class="title">Physical conditioning status <span style="color:var(--muted);font:500 .6rem var(--mono);letter-spacing:.08em">CALCULATED</span></div>'
        '<div class="sub">Tracks musculoskeletal, cardiovascular, and recovery countermeasure signals that help offset microgravity-induced deconditioning — reduced mechanical loading that can reduce muscle strength, bone mineral density, and aerobic capacity over time. '
        'The ring reflects only the physical-domain subset of your logged readings; thresholds are illustrative decision-support ranges, not clinical limits.</div></div>'
        f'<div class="pw-overview-meta"><div>MONITORING PERIOD<br><strong>{_elapsed_label(history)}</strong></div><div>LAST ASSESSMENT<br><strong>{_last_assessment_label(history)}</strong></div><div>STATUS<br><strong>{state}</strong></div></div>'
        "</div></div>",
        unsafe_allow_html=True,
    )


def _render_training_module(history: pd.DataFrame) -> None:
    render_section_bar("Training & exercise monitoring", "exercise compliance · measured from logged check-ins")
    daily_totals = _daily_exercise_totals(history)
    today_utc = pd.Timestamp.now(tz="UTC").floor("D")
    recent_minutes = float(daily_totals.loc[(daily_totals.index >= today_utc - pd.Timedelta(days=6)) & (daily_totals.index <= today_utc)].sum()) if not daily_totals.empty else 0.0
    trained_days, flags = _training_frequency(history)
    trained_timestamps = daily_totals[daily_totals > 0].index
    streak = current_streak(trained_timestamps)
    bars = "".join(f'<div class="pw-freq-day{" done" if flag else ""}"></div>' for flag in flags)
    grip = next((item for item in st.session_state["last_results"] if item.get("id") == "grip_strength_pct"), None)
    grip_status = grip.get("status", "unknown") if grip else "unknown"
    grip_tone = "good" if grip_status == "normal" else "warn" if grip_status == "attention" else "bad" if grip_status == "critical" else "muted"
    grip_reading = grip.get("value") if grip else None
    strength_value = "At baseline" if grip_status == "normal" else "Review" if grip_status == "critical" else "Near target" if grip_status == "attention" else "—"
    strength_detail = "No functional strength check-in" if grip_reading is None else f"Grip strength · {grip_reading:g}% of personal baseline"

    left, center, right = st.columns([1, 1.35, 1], gap="medium")
    with left:
        with st.container(key="pw-training-left", border=True):
            st.markdown('<div class="pw-panel-kicker">WEEKLY LOAD</div>', unsafe_allow_html=True)
            render_summary_cards([
                {"label": "Weekly exercise", "value": f"{recent_minutes:.0f} min", "detail": f"of {WEEKLY_TARGET_MIN:.0f} min target", "tone": "good" if recent_minutes >= WEEKLY_TARGET_MIN else "warn"},
            ], columns=1)
            st.progress(min(max(recent_minutes / WEEKLY_TARGET_MIN, 0.0), 1.0))
            st.markdown('<div class="pw-panel-kicker pw-frequency-label">TRAINING FREQUENCY</div>', unsafe_allow_html=True)
            render_summary_cards([
                {"label": "Days trained", "value": f"{trained_days} / {FREQUENCY_WINDOW} d", "detail": "with a logged session", "tone": "good" if trained_days >= FREQUENCY_WINDOW * 0.5 else "warn"},
            ], columns=1)
            st.markdown(f'<div class="pw-freq-track">{bars}</div><div class="pw-frequency-caption">LAST {FREQUENCY_WINDOW} DAYS</div>', unsafe_allow_html=True)

    with center:
        with st.container(key="pw-training-center", border=True):
            st.markdown('<div class="pw-panel-kicker">EXERCISE MODULE</div>', unsafe_allow_html=True)
            exercise = st.selectbox("Choose an exercise", list(EXERCISE_DEMOS), key="physical_exercise_choice")
            demo = EXERCISE_DEMOS[exercise]
            st.image(str(demo["image"]), width=300)
            st.caption(demo["focus"])
            st.markdown('<div class="pw-panel-kicker pw-log-label">LOG COMPLETED TIME</div>', unsafe_allow_html=True)
            minutes = st.number_input("Minutes completed", min_value=1, max_value=180, value=20, step=5, key="physical_exercise_minutes")
            if st.button("Add exercise time", key="physical_add_exercise_time", type="primary", use_container_width=True):
                today = pd.Timestamp.now(tz="UTC").floor("D")
                today_total = int(daily_totals.get(today, 0))
                save_check_in({"exercise_minutes": today_total + int(minutes)}, datetime.now(timezone.utc), event_type="exercise")
                st.success(f"{int(minutes)} minutes added for {exercise}.")
                st.rerun()

    with right:
        with st.container(key="pw-training-right", border=True):
            st.markdown('<div class="pw-panel-kicker">PERFORMANCE STATUS</div>', unsafe_allow_html=True)
            render_summary_cards([
                {"label": "Session streak", "value": f"{streak} d", "detail": "consecutive days trained", "tone": "good"},
            ], columns=1)
            st.markdown('<div class="pw-status-spacer"></div>', unsafe_allow_html=True)
            render_summary_cards([
                {"label": "Functional strength", "value": strength_value, "detail": strength_detail, "tone": grip_tone},
            ], columns=1)


def _render_musculoskeletal_module(results: list[dict], history: pd.DataFrame) -> None:
    render_section_bar("Musculoskeletal health", "microgravity-induced atrophy and bone-density context")
    grip = next((item for item in results if item.get("id") == "grip_strength_pct"), None)
    trend = trend_for(history, "grip_strength_pct")
    tone = "good" if grip and grip.get("status") == "normal" else "warn" if grip and grip.get("status") == "attention" else "bad" if grip and grip.get("status") == "critical" else "muted"
    value_text = "—" if not grip or grip.get("value") is None else f'{grip["value"]:g} %'
    st.markdown(
        f'<div class="panel"><div class="panel-title">Grip strength vs. personal baseline <span>MEASURED</span></div>'
        f'<div class="metric-card" style="margin-bottom:0"><div class="label">Functional strength</div><div class="number {tone}">{value_text}</div>'
        f'<div class="detail">{grip.get("status_label", "No reading") if grip else "No reading"}</div>'
        f'<div class="trend {trend["direction"]}">{"↑" if trend["direction"]=="up" else "↓" if trend["direction"]=="down" else "→"} {trend["label"]}</div></div>'
        f'<p style="color:var(--muted);font-size:.74rem;line-height:1.55;margin:.9rem 0 0">{INDICATORS["grip_strength_pct"]["why_exam"]}</p></div>',
        unsafe_allow_html=True,
    )


def _render_recovery_module(physical_results: list[dict], history: pd.DataFrame) -> None:
    render_section_bar("Recovery & physical readiness", "sleep, hydration, and training-load balance")
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Recovery signals <span>MEASURED</span></div>', unsafe_allow_html=True)
            render_signal_rows(sort_results(_selected_results(physical_results, RECOVERY_INDICATORS)))
    with right:
        balance = _recovery_balance(history)
        emphasis_class = " nominal" if balance["tone"] == "good" else ""
        status_class = "" if balance["tone"] == "good" else "attention"
        st.markdown(
            f'<div class="panel"><div class="panel-title">Training load vs. recovery <span>CALCULATED</span></div>'
            f'<div class="action-emphasis{emphasis_class}"><span class="status-text {status_class}">{balance["label"].upper()}</span>'
            f'<strong>{balance["label"]}</strong><p>{balance["detail"]}</p></div>'
            '<p style="color:var(--muted);font-size:.7rem;line-height:1.5;margin-top:.8rem">Derived by comparing your own logged sleep-duration and exercise-minute trends — not a clinical fatigue score.</p></div>',
            unsafe_allow_html=True,
        )


def _render_analytics_module(history: pd.DataFrame) -> None:
    render_section_bar("Physical performance analytics", "measured trends · last mission days")
    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        st.markdown('<div class="panel-title">Exercise minutes · last 7 days <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_bar_chart(history, "exercise_minutes", INDICATORS, None)
    with top_right:
        st.markdown('<div class="panel-title">Grip strength vs. personal baseline <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_history_chart(history, "grip_strength_pct", INDICATORS, None, color="#4ED6B0")
    bottom_left, bottom_right = st.columns(2, gap="large")
    with bottom_left:
        st.markdown('<div class="panel-title">Resting heart rate trend <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_history_chart(history, "heart_rate", INDICATORS, None, color="#4D8DFF")
    with bottom_right:
        st.markdown('<div class="panel-title">Sleep duration · recovery window <span>MEASURED</span></div>', unsafe_allow_html=True)
        render_history_chart(history, "sleep_duration", INDICATORS, None, color="#36D6E7")


def _render_recommendations(physical_results: list[dict]) -> None:
    render_section_bar("Training recommendations", "general educational guidance, not a clinical directive")
    cards = _recommendation_cards(physical_results)
    if not cards:
        st.info("No physical-wellness readings are available yet. Complete a check-in to unlock tailored guidance.")
    for index, (label, status, action) in enumerate(cards, start=1):
        st.markdown(
            f'<div class="action-card"><div class="step">{index:02d}</div><div><strong>{label}</strong>'
            f'<span class="action-status {status}">{status.upper()}</span><p>{action}</p></div></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="info-panel" style="margin-top:.6rem"><div class="panel-title">Scope of this guidance <span>EDUCATIONAL</span></div>'
        "<p>Recommendations above are generated from your own indicator statuses using the mission indicator library's pre-written guidance text. They are decision support for a self-assessment prototype — not a diagnosis, and not a substitute for the mission medical plan, exercise specialist, or flight-surgeon direction.</p></div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    """Render the redesigned Physical Wellness dashboard."""
    initialize_state()
    history = st.session_state["history"]
    results = st.session_state["last_results"]
    physical_results = _selected_results(results, PHYSICAL_INDICATORS)
    score = readiness_score(physical_results)
    state = readiness_state(score, physical_results)

    render_section_header("Physical Wellness", SECTION_SUBTITLES["Physical Wellness"], state)
    _render_overview(score, state, history)
    render_alert(state)

    render_section_bar("Key performance indicators", "measured from your logged check-ins · trend vs. recent history")
    render_indicator_cards(results, PHYSICAL_INDICATORS, INDICATORS, columns=5, history=history)

    _render_training_module(history)
    _render_analytics_module(history)
