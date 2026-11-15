"""Shared section header and mission-status presentation."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from config import SECTION_SUBTITLES


def render_section_header(title: str, subtitle: str | None = None, state: str | None = None) -> None:
    """Render a consistent page title, subtitle, and current mission status."""
    subtitle = subtitle or SECTION_SUBTITLES.get(title, "Mission health information and crew support tools.")
    status = state or "NOMINAL"
    status_class = status.lower()
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    st.markdown(
        f'<div class="hero"><div><div class="kicker">Crew health command · live self-assessment</div><h1>{title}</h1><div class="subhead">{subtitle}</div></div><div class="hero-status {status_class}"><div class="label">System status</div><div class="value">{status}</div><div class="detail">Last reading · {now}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_section_bar(title: str, note: str = "") -> None:
    """Render the compact title row used above dashboard panels."""
    icons = {
        "Core physiological signals": "♥",
        "Telemetry coverage": "◌",
        "Environmental history": "⌁",
        "Environmental notifications": "△",
        "Crew health map": "◉",
        "Baseline trend": "↗",
    }
    icon = icons.get(title, "·")
    st.markdown(f'<div class="section-bar"><div class="section-title"><span class="section-icon">{icon}</span>{title}</div><div class="section-note">{note}</div></div>', unsafe_allow_html=True)
