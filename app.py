"""AstroCare Streamlit entry point and section router."""

from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar
from config import APP_ICON, APP_TITLE, SECTION_ORDER, SECTION_SUBTITLES, THEME_PATH
from sections import health_monitoring, mental_wellness, mission_support, physical_wellness, space_environment
from state import initialize_state


SECTION_RENDERERS = {
    "Health Monitoring": health_monitoring,
    "Physical Wellness": physical_wellness,
    "Mental Wellness": mental_wellness,
    "Space Environment": space_environment,
    "Mission Support": mission_support,
}


def inject_css() -> None:
    """Load the shared theme from disk so frontend styling has one owner."""
    try:
        theme = THEME_PATH.read_text(encoding="utf-8")
    except OSError:
        theme = ""
    st.markdown(f"<style>{theme}</style>", unsafe_allow_html=True)


def load_state() -> None:
    """Backward-compatible wrapper around the shared session-state initializer."""
    initialize_state()


def main() -> None:
    """Configure the page, initialize shared state, and render the selected section."""
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
    inject_css()
    load_state()
    render_sidebar()

    selected = st.radio("Mission dashboard", SECTION_ORDER, horizontal=True, label_visibility="collapsed", key="dashboard_section")
    SECTION_RENDERERS[selected].render()
    st.markdown(
        f'<div class="footnote">Prototype for exploration-health design · simulated readings · not medical advice · {SECTION_SUBTITLES[selected]} Thresholds are illustrative and must be replaced by mission-approved clinical rules before operational use.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

