"""Interactive body-system overview used by Health Monitoring."""

from __future__ import annotations

from typing import Any

import streamlit as st


SYSTEMS: dict[str, dict[str, Any]] = {
    "Cardiovascular": {
        "match": {"Cardiovascular"},
        "function": "Circulates blood and adapts to fluid redistribution and changing cardiovascular loading in altered gravity.",
        "risks": "Fluid shifts, deconditioning, and workload can change cardiovascular responses in flight.",
        "action": "Repeat unusual readings after a safe rest period and follow the crew medical officer’s approved protocol.",
        "class": "heart",
    },
    "Respiratory": {
        "match": {"Respiratory"},
        "function": "Supports oxygen exchange and crew performance in a closed habitat or suit environment.",
        "risks": "Sensor quality, cabin or suit context, and environmental conditions can affect oxygenation signals.",
        "action": "Confirm sensor fit and environmental context before escalating the signal through mission procedures.",
        "class": "lungs",
    },
    "Musculoskeletal": {
        "match": {"Musculoskeletal"},
        "function": "Maintains strength and movement while exercise countermeasures offset unloading in microgravity.",
        "risks": "Reduced loading can affect muscle strength, bone health, and aerobic capacity over time.",
        "action": "Keep the approved exercise plan and report persistent functional change rather than chasing a target while unwell.",
        "class": "muscle",
    },
    "Nervous system": {
        "match": {"Cognition", "Behavioral health"},
        "function": "Coordinates cognition, mood, attention, reaction time, and team performance.",
        "risks": "Sleep loss, stress, isolation, workload, and radiation-related concerns can affect performance.",
        "action": "Protect recovery, stay connected to the crew, and use the approved behavioral-health support path.",
        "class": "brain",
    },
    "Recovery & fluid": {
        "match": {"Recovery", "Renal / fluid balance"},
        "function": "Supports sleep, hydration, and recovery routines that protect daily readiness.",
        "risks": "Fluid shifts, workload, and circadian disruption can compound fatigue and urinary-health concerns.",
        "action": "Protect the next sleep and hydration window, record context, and ask the medical team about persistent changes.",
        "class": "environment",
    },
    "Space environment": {
        "match": {"Cabin systems", "Radiation exposure"},
        "function": "Monitors habitat conditions that can directly influence crew physiology and cognition.",
        "risks": "Air quality and ionizing radiation are environmental hazards requiring operational context.",
        "action": "Follow vehicle alarms, radiation-event procedures, and operations direction; do not improvise countermeasures.",
        "class": "environment",
    },
}


def _system_results(system: str, results: list[dict[str, Any]], indicators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    matches = SYSTEMS[system]["match"]
    return [result for result in results if indicators.get(result.get("id"), {}).get("system") in matches]


def _system_state(results: list[dict[str, Any]]) -> str:
    return min((result.get("status", "unknown") for result in results), key=lambda status: {"critical": 0, "attention": 1, "normal": 2, "unknown": 3}.get(status, 3), default="unknown")


def _format_measurement(item: dict[str, Any]) -> str:
    value = item.get("value")
    return "—" if value is None else f'{value:g} {item.get("unit", "")}'


def render_body_map(results: list[dict[str, Any]], indicators: dict[str, dict[str, Any]]) -> None:
    """Render a clickable body-system map and selected-system detail panel."""
    st.markdown('<div class="body-stage" aria-label="Interactive body-system status map"><div class="body-figure"><div class="body-head"></div><div class="body-neck"></div><div class="body-torso"></div><div class="body-arm left"></div><div class="body-arm right"></div><div class="body-leg left"></div><div class="body-leg right"></div><div class="body-hot brain"></div><div class="body-hot lungs"></div><div class="body-hot heart"></div><div class="body-hot muscle"></div><div class="body-hot environment"></div></div></div><div class="body-legend"><span><b>●</b>select a system below</span></div>', unsafe_allow_html=True)
    names = list(SYSTEMS)
    columns = st.columns(3)
    for index, system in enumerate(names):
        related = _system_results(system, results, indicators)
        state = _system_state(related)
        with columns[index % len(columns)]:
            if st.button(system, key=f"body_system_{index}", use_container_width=True):
                st.session_state["selected_system"] = system
            st.caption({"normal": "nominal", "attention": "watch", "critical": "escalate", "unknown": "no reading"}.get(state, "no reading"))

    selected = st.session_state.get("selected_system", "Cardiovascular")
    if selected not in SYSTEMS:
        selected = "Cardiovascular"
    related = _system_results(selected, results, indicators)
    definition = SYSTEMS[selected]
    status = _system_state(related)
    status_label = {"normal": "NOMINAL", "attention": "WATCH", "critical": "ESCALATE", "unknown": "NO READING"}[status]
    measurement_rows = "".join(
        f'<div class="system-reading"><span>{indicators[item["id"]].get("short_label", item["label"])}</span><strong>{_format_measurement(item)}</strong></div>'
        for item in related
        if item.get("id") in indicators
    ) or '<div class="system-reading"><span>No readings in this system</span><strong>—</strong></div>'
    st.markdown(
        f'<div class="detail-box"><div class="eyebrow">Selected system · {selected} <span class="status-inline {status}">{status_label}</span></div><h3>{definition["function"]}</h3><p><strong>Current measurements</strong></p>{measurement_rows}<p><strong>Spaceflight risk:</strong> {definition["risks"]}</p><p><strong>Preventive action:</strong> {definition["action"]}</p></div>',
        unsafe_allow_html=True,
    )

