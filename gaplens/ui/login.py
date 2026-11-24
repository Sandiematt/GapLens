"""Simple center-aligned login screen for Student and Faculty portals.

Submitting valid credentials for the chosen role unlocks only that role's pages.
"""
from __future__ import annotations

import streamlit as st

import config
from ui import components, loader, profile, theme
from ui.flash import flash, show_flash

LOGIN_TAB_KEY = "login_role_tab"
LOGIN_ROLE_KEY = "login_selected_role"

TAB_TO_ROLE = {
    "Student Login": "Student",
    "Faculty Login": "Faculty",
}
ROLE_TO_TAB = {v: k for k, v in TAB_TO_ROLE.items()}

ICON_STUDENT = (
    '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M22 10l-10-5L2 10l10 5 10-5z"/>'
    '<path d="M6 12v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/></svg>'
)
ICON_FACULTY = (
    '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="12" rx="2"/>'
    '<line x1="8" y1="20" x2="16" y2="20"/>'
    '<line x1="12" y1="16" x2="12" y2="20"/></svg>'
)

PORTAL_COPY = {
    "Student": {
        "head_cls": "gl-login-head-student",
        "badge_cls": "gl-login-badge-student",
        "icon": ICON_STUDENT,
        "form_desc": "Enter your student username and password to sign in.",
        "placeholder_user": "student",
    },
    "Faculty": {
        "head_cls": "gl-login-head-faculty",
        "badge_cls": "gl-login-badge-faculty",
        "icon": ICON_FACULTY,
        "form_desc": "Enter your faculty username and password to sign in.",
        "placeholder_user": "admin",
    },
}


def _on_login_tab_change() -> None:
    chosen = st.session_state.get(LOGIN_TAB_KEY)
    if chosen in TAB_TO_ROLE:
        st.session_state[LOGIN_ROLE_KEY] = TAB_TO_ROLE[chosen]


def render_login() -> None:
    """Render a simple center-aligned login screen with Student / Faculty switcher."""
    theme.hide_sidebar()

    role = st.session_state.get(LOGIN_ROLE_KEY, "Student")
    if role not in config.ROLES:
        role = "Student"
        st.session_state[LOGIN_ROLE_KEY] = role

    copy = PORTAL_COPY[role]

    with st.container(key="login_shell"):
        components.render(
            f'<div class="gl-login-brand">'
            f'{components.home_topbar_brand()}'
            f'<div class="gl-login-tagline">{config.APP_TAGLINE}</div>'
            f'</div>'
        )

        with st.container(key="login_topbar"):
            st.session_state[LOGIN_TAB_KEY] = ROLE_TO_TAB[role]
            st.segmented_control(
                "Login portal",
                list(TAB_TO_ROLE),
                key=LOGIN_TAB_KEY,
                width="stretch",
                label_visibility="collapsed",
                on_change=_on_login_tab_change,
            )

        show_flash()

        with st.container(border=True, key="card_login"):
            components.render(
                f'<div class="gl-login-head {copy["head_cls"]}">'
                f'<div class="gl-login-badge {copy["badge_cls"]}">{copy["icon"]}</div>'
                f'<div class="gl-login-title">{role} Login</div>'
                f'</div>'
            )
            with st.container(key="login_form_body"):
                components.render(f'<p class="gl-login-desc">{copy["form_desc"]}</p>')
                with st.form(f"login_form_{role}", clear_on_submit=False, border=False):
                    username = st.text_input(
                        "Username",
                        key=f"login_user_{role}",
                        placeholder=copy["placeholder_user"],
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key=f"login_pass_{role}",
                        placeholder="Enter password",
                    )
                    submitted = st.form_submit_button(
                        f"Sign in to {role} Portal",
                        type="primary",
                        width="stretch",
                    )

                if submitted:
                    if not username.strip() or not password:
                        st.error("Please enter both username and password.")
                    elif profile.authenticate(role, username, password):
                        steps = (
                            [
                                (25, "Verifying student credentials…"),
                                (65, "Loading enrolled subjects, marks & goals…"),
                                (100, "Opening Student Portal…"),
                            ]
                            if role == "Student"
                            else [
                                (25, "Verifying faculty credentials…"),
                                (65, "Loading courses, papers & class insights…"),
                                (100, "Opening Faculty Portal…"),
                            ]
                        )
                        loader.show_loading_bar(f"Signing in · {role} Portal", steps)
                        profile.login(role, username)
                        flash(f"Signed in to the {role} portal.")
                        st.rerun()
                    else:
                        other = profile.matching_role(username, password)
                        if other:
                            st.error(
                                f"Those credentials belong to {other} Login. "
                                f"Switch to {other} Login above."
                            )
                        else:
                            st.error(f"Invalid {role.lower()} username or password.")

        components.render(
            f'<div class="gl-login-footer">{config.APP_NAME} &middot; {config.APP_TAGLINE} &middot; 2026</div>'
        )


def render_faculty_switch_login() -> None:
    """Render a dedicated Faculty login screen when switching from the Student portal."""
    theme.hide_sidebar()
    copy = PORTAL_COPY["Faculty"]

    with st.container(key="login_shell"):
        components.render(
            f'<div class="gl-login-brand">'
            f'{components.home_topbar_brand()}'
            f'<div class="gl-login-tagline">{config.APP_TAGLINE}</div>'
            f'</div>'
        )

        show_flash()

        with st.container(border=True, key="card_login"):
            components.render(
                f'<div class="gl-login-head {copy["head_cls"]}">'
                f'<div class="gl-login-badge {copy["badge_cls"]}">{copy["icon"]}</div>'
                f'<div class="gl-login-title">Faculty Login</div>'
                f'</div>'
            )
            with st.container(key="login_form_body"):
                components.render(
                    '<p class="gl-login-desc">'
                    'Enter your faculty username and password to switch to the Faculty portal.'
                    '</p>'
                )
                with st.form("switch_faculty_form", clear_on_submit=False, border=False):
                    username = st.text_input(
                        "Username",
                        key="switch_faculty_user",
                        placeholder=copy["placeholder_user"],
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="switch_faculty_pass",
                        placeholder="Enter password",
                    )
                    submitted = st.form_submit_button(
                        "Sign in to Faculty Portal",
                        type="primary",
                        width="stretch",
                    )

                if submitted:
                    if not username.strip() or not password:
                        st.error("Please enter both username and password.")
                    elif profile.authenticate("Faculty", username, password):
                        loader.show_loading_bar(
                            "Signing in · Faculty Portal",
                            [
                                (25, "Verifying faculty credentials…"),
                                (65, "Loading courses, papers & class insights…"),
                                (100, "Opening Faculty Portal…"),
                            ],
                        )
                        profile.switch_to_faculty(username)
                        flash("Switched to the Faculty portal.")
                        st.rerun()
                    elif profile.matching_role(username, password) == "Student":
                        st.error(
                            "Those credentials belong to Student Login. "
                            "Enter Faculty credentials to switch."
                        )
                    else:
                        st.error("Invalid faculty username or password.")

                if st.button(
                    "Back to Student Portal",
                    key="switch_faculty_cancel",
                    icon=":material/arrow_back:",
                    width="stretch",
                ):
                    profile.cancel_faculty_switch()
                    st.rerun()

        components.render(
            f'<div class="gl-login-footer">{config.APP_NAME} &middot; {config.APP_TAGLINE} &middot; 2026</div>'
        )
