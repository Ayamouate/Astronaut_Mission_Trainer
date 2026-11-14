"""Metric-card primitives shared by all dashboard sections."""

from __future__ import annotations

from typing import Any, Iterable

import streamlit as st

from gamification import current_streak


def render_summary_cards(cards: Iterable[dict[str, str]], columns: int | None = None) -> None:
    """Render a row of consistent AstroCare summary cards."""
    cards = list(cards)
    if not cards:
        return
    cols = st.columns(columns or min(len(cards), 4))
    for column, card in zip(cols * ((len(cards) + len(cols) - 1) // len(cols)), cards):
        with column:
            tone = card.get("tone", "good")
            st.markdown(
                f'<div class="metric-card"><div class="label">{card.get("label", "Metric")}</div><div class="number {tone}">{card.get("value", "—")}</div><div class="detail">{card.get("detail", "")}</div></div>',
                unsafe_allow_html=True,
            )


def render_readiness_cards(score: int, state: str, results: list[dict[str, Any]], checkins: int) -> None:
    """Render the standard readiness, signal, streak, and sync cards."""
    attention = sum(item.get("status") == "attention" for item in results)
    critical = sum(item.get("status") == "critical" for item in results)
    score_value = f"{score}" if score else "—"
    render_summary_cards(
        [
            {"label": "Readiness index", "value": score_value, "detail": "out of 100 · decision support", "tone": "good" if state == "NOMINAL" else "warn" if state == "WATCH" else "bad"},
            {"label": "Signal review", "value": f"{attention + critical:02d}", "detail": f"{critical} escalate · {attention} watch", "tone": "bad" if critical else "warn" if attention else "good"},
            {"label": "Check-in streak", "value": f"{current_streak(checkins):02d} d", "detail": "keep the rhythm", "tone": "good"},
            {"label": "Next sync", "value": "02:00", "detail": "UTC · scheduled window", "tone": "good"},
        ],
        columns=4,
    )


def render_indicator_cards(results: list[dict[str, Any]], indicator_ids: Iterable[str], indicators: dict[str, dict[str, Any]], columns: int = 4) -> None:
    """Render current values for a chosen set of indicator IDs."""
    result_by_id = {result.get("id"): result for result in results}
    cards = []
    for indicator_id in indicator_ids:
        indicator = indicators.get(indicator_id)
        if not indicator:
            continue
        result = result_by_id.get(indicator_id, {})
        status = result.get("status", "unknown")
        value = result.get("value")
        value_text = "—" if value is None else f"{value:g}"
        tone = "good" if status == "normal" else "warn" if status == "attention" else "bad" if status == "critical" else "muted"
        cards.append({"label": indicator.get("short_label", indicator.get("label", indicator_id)), "value": f'{value_text} {indicator.get("unit", "")}', "detail": result.get("status_label", "No reading"), "tone": tone})
    render_summary_cards(cards, columns=columns)

