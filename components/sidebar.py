"""Shared mission-profile sidebar."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    """Render the persistent AstroCare mission profile and safety note."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">✦</div><div class="brand-name">ASTRO<span>CARE</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-label">Mission profile</div><div class="mission-card"><div class="eyebrow">MARS TRANSIT · SIMULATION</div><div class="title">Ares / Crew 04</div><div class="sub">Sol 164 · outbound · 3 crew</div></div><div style="height:.8rem"></div>', unsafe_allow_html=True)
        for label, value in [
            ("Distance from Earth", "12m 41s"),
            ("Gravity field", "0.38 g"),
            ("Cabin status", "nominal"),
            ("Last sync", "13:58 UTC"),
        ]:
            st.markdown(f'<div class="side-stat"><span>{label}</span><strong>{value}</strong></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="height:1.5rem"></div><div class="sidebar-label">Safety note</div><p class="sidebar-copy">Use approved devices and mission procedures. A flagged value is a reason to repeat and escalate—not a diagnosis.</p><div style="height:1.5rem"></div><div class="sidebar-label">Protocol</div><div class="side-stat"><span>Medical link</span><strong class="side-good">READY</strong></div><div class="side-stat"><span>Emergency mode</span><strong>STANDBY</strong></div>',
            unsafe_allow_html=True,
        )

