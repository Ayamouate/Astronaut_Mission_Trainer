"""Shared mission-profile sidebar."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    """Render AstroCare identity and the primary navigation in the sidebar."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">?</div><div class="brand-name">ASTRO<span>CARE</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-label">Crew health</div>', unsafe_allow_html=True)
