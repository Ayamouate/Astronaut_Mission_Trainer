"""Image-based health-system map with live, selectable astronaut readings."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import streamlit as st


TWIN_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "human_digital_twin.jpg"

SYSTEMS: dict[str, dict[str, Any]] = {
    "Cardiovascular": {
        "match": {"Cardiovascular"}, "function": "Circulates blood and adapts to fluid redistribution and changing cardiovascular loading in altered gravity.",
        "risks": "Fluid shifts, deconditioning, and workload can change cardiovascular responses in flight.",
        "action": "Repeat unusual readings after a safe rest period and follow the crew medical officer's approved protocol.",
        "callout": "CARDIAC MODEL", "detail": "CARDIOVASCULAR SIGNALS", "position": (53.0, 32.0, "right"),
    },
    "Respiratory": {
        "match": {"Respiratory"}, "function": "Supports oxygen exchange and crew performance in a closed habitat or suit environment.",
        "risks": "Sensor quality, cabin or suit context, and environmental conditions can affect oxygenation signals.",
        "action": "Confirm sensor fit and environmental context before escalating the signal through mission procedures.",
        "callout": "RESPIRATORY", "detail": "LUNG / OXYGEN SIGNALS", "position": (47.8, 33.5, "left"),
    },
    "Musculoskeletal": {
        "match": {"Musculoskeletal"}, "function": "Maintains strength and movement while exercise countermeasures offset unloading in microgravity.",
        "risks": "Reduced loading can affect muscle strength, bone health, and aerobic capacity over time.",
        "action": "Keep the approved exercise plan and report persistent functional change rather than chasing a target while unwell.",
        "callout": "SPINAL AXIS", "detail": "MUSCLE / EXERCISE SIGNALS", "position": (50.2, 43.0, "left"),
    },
    "Nervous system": {
        "match": {"Cognition", "Behavioral health", "Recovery"}, "function": "Coordinates sleep, cognition, mood, attention, reaction time, and team performance.",
        "risks": "Sleep loss, stress, isolation, workload, and radiation-related concerns can affect performance.",
        "action": "Protect recovery, stay connected to the crew, and use the approved behavioral-health support path.",
        "callout": "NEURAL MAP", "detail": "SLEEP / MOOD / COGNITION", "position": (50.4, 16.5, "right"),
    },
    "Recovery & fluid": {
        "match": {"Recovery", "Renal / fluid balance", "Whole body"}, "function": "Connects sleep, hydration, temperature, and whole-body signals to daily recovery.",
        "risks": "Fluid shifts, workload, and circadian disruption can compound fatigue and urinary-health concerns.",
        "action": "Protect the next sleep and hydration window, record context, and ask the medical team about persistent changes.",
        "callout": "RECOVERY & FLUID", "detail": "SLEEP / HYDRATION SIGNALS", "position": (50.2, 51.0, "right"),
    },
    "Space environment": {
        "match": {"Cabin systems", "Radiation exposure"}, "function": "Monitors habitat conditions that can directly influence crew physiology and cognition.",
        "risks": "Air quality and ionizing radiation are environmental hazards requiring operational context.",
        "action": "Follow vehicle alarms, radiation-event procedures, and operations direction; do not improvise countermeasures.",
        "callout": "SPACE ENVIRONMENT", "detail": "CABIN / RADIATION SIGNALS", "position": (62.2, 78.0, "left"),
    },
}

STATUS_COLORS = {"normal": "#42e8d2", "attention": "#f2bd62", "critical": "#ff7187", "unknown": "#648a96"}
STATUS_LABELS = {"normal": "NOMINAL", "attention": "WATCH", "critical": "ESCALATE", "unknown": "NO READING"}


def _system_results(system: str, results: list[dict[str, Any]], indicators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    matches = SYSTEMS[system]["match"]
    return [result for result in results if indicators.get(result.get("id"), {}).get("system") in matches]


def _system_state(results: list[dict[str, Any]]) -> str:
    priority = {"critical": 0, "attention": 1, "normal": 2, "unknown": 3}
    return min((result.get("status", "unknown") for result in results), key=lambda status: priority.get(status, 3), default="unknown")


def _format_measurement(item: dict[str, Any]) -> str:
    value = item.get("value")
    return "—" if value is None else f'{value:g} {item.get("unit", "")}'


def _state_color(system: str, status: str) -> str:
    if status == "normal" and system in {"Nervous system", "Recovery & fluid"}:
        return "#61adff"
    if status == "attention" and system == "Space environment":
        return "#f4d35e"
    return STATUS_COLORS[status]


def _state_text(system: str, status: str) -> str:
    if status == "attention" and system == "Space environment":
        return "MONITOR"
    if status == "attention":
        return "ATTENTION NEEDED"
    return STATUS_LABELS[status]


def _image_map(results: list[dict[str, Any]], indicators: dict[str, dict[str, Any]], selected: str) -> str:
    """Compose the live twin UI around the supplied human image."""
    encoded = base64.b64encode(TWIN_IMAGE.read_bytes()).decode("ascii")
    overlays = []
    markers = []
    leaders = []
    for system, definition in SYSTEMS.items():
        status = _system_state(_system_results(system, results, indicators))
        color = _state_color(system, status)
        x, y, side = definition["position"]
        label_left = "66%" if side == "right" else "10%"
        label_top = {"Nervous system": "14.2%", "Cardiovascular": "29.5%", "Respiratory": "31%", "Musculoskeletal": "40.75%", "Recovery & fluid": "48.75%", "Space environment": "70%"}[system]
        waveform = '<svg class="status-wave" viewBox="0 0 90 20" aria-hidden="true"><path d="M1 11H18L23 9L28 11H39L44 4L49 17L54 8L58 11H89"/></svg>' if system == "Respiratory" else ""
        selected_class = " selected" if system == selected else ""
        no_leader = " no-leader" if system == "Space environment" else ""
        overlays.append(
            f'<div class="twin-live-callout {side}{selected_class}{no_leader}" style="--signal:{color};left:{label_left};top:{label_top}">'
            f'<span>{_state_text(system, status)} / {system.upper()}</span><strong>{definition["callout"]}</strong><small>{definition["detail"]}</small>{waveform}</div>'
        )
        if system != "Space environment":
            anchor_x = 792 if side == "right" else 324
            anchor_y = float(label_top[:-1]) * 8 + 18
            target_x, target_y = x * 12, y * 8
            leaders.append(f'<path class="twin-leader" style="--signal:{color}" d="M{anchor_x} {anchor_y} L{target_x} {target_y}"/>')
            selected_marker = " selected" if system == selected else ""
            markers.append(f'<span class="twin-live-marker{selected_marker}" title="{system}: {STATUS_LABELS[status]}" style="--signal:{color};left:{x}%;top:{y}%"></span>')
    selected_results = _system_results(selected, results, indicators)
    selected_status = _system_state(selected_results)
    selected_definition = SYSTEMS[selected]
    reading_rows = "".join(
        f'<div class="selected-reading"><span>{item.get("label", "Signal")}</span><strong>{_format_measurement(item)}</strong></div>'
        for item in selected_results[:3]
    ) or '<div class="selected-reading"><span>Readings</span><strong>Not recorded</strong></div>'
    sleep_result = next((item for item in results if item.get("id") == "sleep_duration"), None)
    if sleep_result and sleep_result.get("value") is not None:
        sleep_flagged = sleep_result.get("status") in {"attention", "critical"}
        recovery_text = f'Low sleep · {_format_measurement(sleep_result)}' if sleep_flagged else f'{_format_measurement(sleep_result)} sleep'
        risk_text = "Fatigue risk · review" if sleep_flagged else "No sleep flag"
    else:
        recovery_text, risk_text = "Not recorded", "Awaiting check-in"
    flagged_action = next((item.get("action") for item in selected_results if item.get("status") in {"attention", "critical"}), None)
    if selected == "Cardiovascular" and not flagged_action and sleep_result and sleep_result.get("status") in {"attention", "critical"}:
        flagged_action = sleep_result.get("action")
    follow_up = flagged_action or selected_definition["action"]
    if len(follow_up) > 105:
        follow_up = follow_up[:102].rsplit(" ", 1)[0] + "…"
    ecg = '<small class="ecg-label">PULSE TRACE · SCHEMATIC</small><svg class="ecg-schematic" viewBox="0 0 180 32" role="img" aria-label="Schematic pulse trace"><path d="M1 17H40L48 15L54 17H72L80 4L88 28L96 12L102 17H179"/></svg>' if selected == "Cardiovascular" else ""
    panel_title = f'{selected_definition["callout"]} SELECTED'
    recovery_row = f'<div class="selected-reading"><span>RECOVERY</span><strong>{recovery_text}</strong></div>' if selected == "Cardiovascular" else ""
    if selected != "Cardiovascular":
        risk_text = selected_definition["risks"]
        if len(risk_text) > 82:
            risk_text = risk_text[:79].rsplit(" ", 1)[0] + "…"
    risk_row = f'<div class="selected-reading"><span>RISK</span><strong>{risk_text}</strong></div>'
    followup_row = f'<div class="selected-followup"><span>FOLLOW-UP</span><p>{follow_up}</p></div>'
    connectivity = "CONNECTED · CHECK-IN DATA" if results else "AWAITING FIRST CHECK-IN"
    return (
        '<div class="digital-twin"><div class="twin-header"><div><strong>Body systems</strong><small>NON-DIAGNOSTIC DASHBOARD</small></div>'
        f'<div class="twin-header-right"><strong>LIVE DIGITAL TWIN</strong><small>CHECK-IN CONNECTIVITY · {connectivity}</small></div></div><div class="twin-image-wrap">'
        f'<img class="twin-image" src="data:image/jpeg;base64,{encoded}" alt="Anterior human digital twin showing respiratory, cardiovascular, nervous, musculoskeletal, recovery, and environmental health systems">'
        f'<svg class="twin-leaders" viewBox="0 0 1200 800" preserveAspectRatio="none" aria-hidden="true">{"".join(leaders)}</svg>{"".join(overlays)}{"".join(markers)}'
        f'<div class="twin-selected-panel" style="--signal:{_state_color(selected, selected_status)}"><div class="selected-panel-title"><small>SELECTED SYSTEM</small><span>{_state_text(selected, selected_status)}</span></div><strong class="selected-system-name">{panel_title}</strong>'
        f'{ecg}{reading_rows}{recovery_row}{risk_row}{followup_row}</div>'
        '</div><div class="twin-footer">SELECT A SYSTEM TO VIEW READINGS, RISKS, &amp; RECOMMENDED FOLLOW-UP <span>(NON-DIAGNOSTIC INTERPRETER)</span></div></div>'
    )


def render_body_map(results: list[dict[str, Any]], indicators: dict[str, dict[str, Any]]) -> None:
    """Render the supplied digital-twin image, live status markers, and details."""
    selected = st.session_state.get("selected_system", "Cardiovascular")
    if selected not in SYSTEMS:
        selected = "Cardiovascular"
    st.markdown(_image_map(results, indicators, selected), unsafe_allow_html=True)
    names = list(SYSTEMS)
    selector_column = st.columns([.14, .72, .14])[1]
    with selector_column:
        for start in range(0, len(names), 3):
            columns = st.columns(3)
            for offset, system in enumerate(names[start:start + 3]):
                index = start + offset
                with columns[offset]:
                    st.button(
                        system,
                        key=f"body_system_{index}",
                        use_container_width=True,
                        type="primary" if st.session_state.get("selected_system") == system else "secondary",
                        on_click=_select_system,
                        args=(system,),
                    )

def _select_system(system: str) -> None:
    st.session_state["selected_system"] = system
