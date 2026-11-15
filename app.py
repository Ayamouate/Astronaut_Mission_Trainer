"""AstroCare Streamlit entry point and section router."""

from __future__ import annotations

import streamlit as st

from auth import authenticate, create_account, get_profile
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


def render_sign_in() -> None:
    """Show account creation and sign-in before opening a personal dashboard."""
    st.markdown("# AstroCare · Astronaut access")
    st.caption("Create a crew profile or sign in to view your personal health dashboard.")
    login_tab, create_tab = st.tabs(["Sign in", "Create astronaut profile"])
    with login_tab:
        with st.form("astronaut_signin"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            valid, result = authenticate(email, password)
            if valid:
                st.session_state["astronaut_email"] = result
                st.rerun()
            st.error(result)
    with create_tab:
        with st.form("astronaut_signup"):
            name = st.text_input("Full name")
            callsign = st.text_input("Crew label / callsign")
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            confirmation = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create profile", type="primary", use_container_width=True)
        if submitted:
            if len(password) < 8:
                st.error("Choose a password with at least 8 characters.")
            elif password != confirmation:
                st.error("The passwords do not match.")
            else:
                created, result = create_account(name, callsign, email, password)
                if created:
                    st.session_state["astronaut_email"] = result
                    st.rerun()
                st.error(result)


def main() -> None:
    """Configure the page, initialize shared state, and render the selected section."""
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
    inject_css()
    load_state()
    astronaut_email = st.session_state.get("astronaut_email")
    if not astronaut_email or not get_profile(astronaut_email):
        render_sign_in()
        return
    profile = get_profile(astronaut_email)
    render_sidebar()
    with st.sidebar:
        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        if st.button(f"??  {profile['name']} ? Profile", key="sidebar_profile", use_container_width=True):
            st.session_state["dashboard_section"] = "Profile"
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    choices = [*SECTION_ORDER, "Profile"]
    selected = st.sidebar.radio("Workspace", choices, label_visibility="collapsed", key="dashboard_section")
    if selected == "Profile":
        st.markdown('<div class="kicker">Crew account</div>', unsafe_allow_html=True)
        st.title("Your profile")
        st.caption("Personal account and mission access")
        st.markdown(f"### {profile['name']}")
        st.write(f"**Crew label:** {profile.get('callsign') or 'Crew member'}")
        st.write(f"**Email:** {profile['email']}")
    else:
        SECTION_RENDERERS[selected].render()
        st.markdown(
            f'<div class="footnote">Prototype for exploration-health design ? simulated readings ? not medical advice ? {SECTION_SUBTITLES[selected]} Thresholds are illustrative and must be replaced by mission-approved clinical rules before operational use.</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

