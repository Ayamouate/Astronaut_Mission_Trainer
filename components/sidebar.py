"""Shared mission identity, profile shortcut, and navigation sidebar."""

from __future__ import annotations

import streamlit as st
from html import escape


def render_sidebar(profile: dict | None = None) -> None:
    """Render AstroCare branding and a profile shortcut above the primary navigation."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">A</div><div><div class="brand-name">ASTRO<span>CARE</span></div><div class="brand-tagline">CREW HEALTH COMMAND</div></div></div>',
            unsafe_allow_html=True,
        )
        if profile:
            display_name = str(profile.get("name") or "Member").strip() or "Member"
            name_parts = display_name.split()
            initial = (
                f"{name_parts[0][0]}{name_parts[-1][0]}"
                if len(name_parts) > 1
                else (name_parts[0][:1] or "C")
            ).upper()
            with st.container(key="sidebar_profile_top"):
                avatar, name = st.columns([0.28, 0.72], vertical_alignment="center", gap="small")
                with avatar:
                    if st.button(initial, key="sidebar_profile_btn", help="Edit profile", width="content"):
                        st.session_state["show_profile"] = not st.session_state.get("show_profile", False)
                with name:
                    st.markdown(f'<div class="sidebar-profile-name">{escape(display_name)}</div>', unsafe_allow_html=True)
