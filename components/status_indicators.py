"""Reusable status banners, pills, and priority signal rows."""

from __future__ import annotations

from typing import Any, Iterable

import streamlit as st

from engine import sort_by_priority


def state_tone(state: str) -> str:
    """Map a readiness state to the CSS tone used by shared components."""
    return {"NOMINAL": "good", "WATCH": "warn", "ESCALATE": "bad"}.get(state, "good")


def render_alert(state: str) -> None:
    """Render the common nominal/watch/escalate status banner."""
    copy = {
        "NOMINAL": ("✓", "NO ACUTE FLAGS", "Your latest check-in is inside the demo baseline. Keep the scheduled monitoring cadence."),
        "WATCH": ("△", "WATCH ITEMS PRESENT", "One or more readings deserve a repeat, a recovery action, or a flight-surgeon review."),
        "ESCALATE": ("!", "ESCALATE TO CREW MEDICAL", "At least one reading is outside the demo safety envelope. Use the approved mission protocol now."),
    }.get(state, ("i", "STATUS UNAVAILABLE", "No evaluated readings are currently available."))
    st.markdown(f'<div class="alert {state.lower()}"><div class="icon">{copy[0]}</div><div><div class="title">{copy[1]}</div><div class="copy">{copy[2]}</div></div></div>', unsafe_allow_html=True)


def render_status_pill(status: str, label: str | None = None) -> None:
    """Render a text-plus-color status label so color is never the only signal."""
    label = label or {"normal": "NOMINAL", "attention": "WATCH", "critical": "ESCALATE", "unknown": "NO READING"}.get(status, status.upper())
    st.markdown(f'<span class="status-pill {status}">{label}</span>', unsafe_allow_html=True)


def sort_results(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort evaluated results with critical signals first."""
    return sort_by_priority(list(results))


def render_signal_rows(results: Iterable[dict[str, Any]], limit: int | None = None) -> None:
    """Render compact, reusable signal rows for any section."""
    ordered = sort_results(results)
    if limit is not None:
        ordered = ordered[:limit]
    if not ordered:
        st.info("No readings are available for this view yet.")
        return
    for result in ordered:
        status = "" if result.get("status") == "normal" else result.get("status", "unknown")
        value = "—" if result.get("value") is None else f'{result["value"]:g} {result.get("unit", "")}'
        st.markdown(
            f'<div class="signal-row"><div class="dot {status}"></div><div class="signal-main"><div class="signal-label">{result.get("label", "Unnamed signal")}</div><div class="signal-message">{result.get("message", "No interpretation available.")}</div></div><div class="signal-value">{value}</div><div class="status-text {status}">{result.get("status_label", "No reading")}</div></div>',
            unsafe_allow_html=True,
        )

