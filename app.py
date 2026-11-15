"""AstroCare Streamlit entry point and section router."""

from __future__ import annotations

import base64

import streamlit as st

from auth import authenticate, create_account, get_profile, update_profile
from components.sidebar import render_sidebar
from config import APP_ICON, APP_TITLE, LOGIN_BACKGROUND_PATH, SECTION_ORDER, SECTION_SUBTITLES, THEME_PATH
from sections import health_monitoring, mental_wellness, mission_overview, physical_wellness, space_environment
from state import initialize_state


SECTION_RENDERERS = {
    "Mission Overview": mission_overview,
    "Health Monitoring": health_monitoring,
    "Physical Wellness": physical_wellness,
    "Mental Wellness": mental_wellness,
    "Space Environment": space_environment,
}

def inject_css() -> None:
    """Load the shared theme from disk so frontend styling has one owner."""
    try:
        theme = THEME_PATH.read_text(encoding="utf-8")
    except OSError:
        theme = ""
    try:
        image_data = base64.b64encode(LOGIN_BACKGROUND_PATH.read_bytes()).decode("ascii")
        theme = theme.replace("__LOGIN_BACKGROUND_IMAGE__", f"data:image/png;base64,{image_data}")
    except OSError:
        theme = theme.replace("__LOGIN_BACKGROUND_IMAGE__", "none")
    st.markdown(f"<style>{theme}</style>", unsafe_allow_html=True)


def load_state() -> None:
    """Backward-compatible wrapper around the shared session-state initializer."""
    initialize_state()


def render_sign_in() -> None:
    """Show account creation and sign-in before opening a personal dashboard."""
    st.markdown(
        '<div class="login-shell"><div class="login-brand"><span class="login-mark">✦</span><div><div class="login-name">ASTRO<span>CARE</span></div><div class="login-overline">CREW HEALTH COMMAND</div></div></div>'
        '<div class="login-copy"><div class="kicker">Secure mission access</div><h1>Health intelligence for the journey beyond Earth.</h1><p>Sign in to review your personal readiness signals, approved check-ins, and operational health guidance.</p></div></div>',
        unsafe_allow_html=True,
    )
    login_tab, create_tab = st.tabs(["Sign in", "Create astronaut profile"])
    with login_tab:
        with st.form("astronaut_signin"):
            email = st.text_input("Email address", key="login_email", placeholder="you@mission.example")
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            if not email.strip() or not password:
                st.error("Enter your email address and password to continue.")
                return
            valid, result = authenticate(email, password)
            if valid:
                st.session_state["astronaut_email"] = result
                st.rerun()
            st.error(result)
    with create_tab:
        with st.form("astronaut_signup"):
            name = st.text_input("Full name")
            email = st.text_input("Email address", placeholder="you@mission.example")
            password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            confirmation = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create profile", type="primary", use_container_width=True)
        if submitted:
            if password != confirmation:
                st.error("The passwords do not match.")
            else:
                created, result = create_account(name, email, password)
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
    render_sidebar(profile)
    selected = st.sidebar.radio(
        "Navigation", SECTION_ORDER, label_visibility="collapsed", key="dashboard_section",
        on_change=lambda: st.session_state.update(show_profile=False),
    )
    with st.sidebar:
        with st.container(key="sidebar_bottom"):
            if st.button("Sign out", key="sidebar_signout", width="stretch"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    if st.session_state.get("show_profile"):
        st.title("Edit profile")
        with st.form("edit_profile"):
            name = st.text_input("Full name", value=profile.get("name", ""))
            email = st.text_input("Email", value=profile.get("email", ""))
            saved = st.form_submit_button("Save changes", type="primary")
        if saved:
            ok, result = update_profile(astronaut_email, name, email)
            if ok:
                st.session_state["astronaut_email"] = result
                st.success("Profile updated.")
                st.rerun()
            st.error(result)
    else:
        SECTION_RENDERERS[selected].render()
        st.markdown(
            f'<div class="footnote">Prototype for exploration-health design ? simulated readings ? not medical advice ? {SECTION_SUBTITLES[selected]} Thresholds are illustrative and must be replaced by mission-approved clinical rules before operational use.</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
