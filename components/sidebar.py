"""Shared mission identity, profile shortcut, and navigation sidebar."""

from __future__ import annotations

import streamlit as st


def render_sidebar(profile: dict | None = None) -> None:
    """Render AstroCare branding and a profile shortcut above the primary navigation."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">A</div><div class="brand-name">ASTRO<span>CARE</span></div></div>',
            unsafe_allow_html=True,
        )
        if profile:
            display_name = str(profile.get("name") or "Crew member").strip() or "Crew member"
            callsign = str(profile.get("callsign") or "").strip()
            initial = (display_name[:1] or "C").upper()
            with st.container(key="sidebar_profile_top"):
                if st.button(initial, key="sidebar_profile_btn", help="Edit profile", width="content"):
                    st.session_state["show_profile"] = not st.session_state.get("show_profile", False)
                callsign_html = f'<span class="sidebar-profile-callsign">{callsign}</span>' if callsign else ""
                st.markdown(f'<div class="sidebar-profile-name">{display_name}{callsign_html}</div>', unsafe_allow_html=True)
