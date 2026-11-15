"""Shared mission-profile sidebar."""

from __future__ import annotations

import streamlit as st


def render_sidebar(profile: dict | None = None) -> None:
    """Render AstroCare identity and the primary navigation in the sidebar."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">A</div><div><div class="brand-name">ASTRO<span>CARE</span></div><div class="brand-tagline">CREW HEALTH COMMAND</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
        if profile:
            name = profile.get("name", "Crew member")
            callsign = profile.get("callsign") or "Unassigned callsign"
            st.markdown(
                f'<div class="mission-card"><div class="eyebrow">ACTIVE CREW MEMBER</div><div class="title">{name}</div><div class="sub">{callsign}</div></div>',
                unsafe_allow_html=True,
            )
