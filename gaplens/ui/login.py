"""Login screen matching the GapLens Editorial Mint & Charcoal layout.

Top bar switches between Student Login and Faculty Login. Submitting valid
credentials for the chosen role unlocks only that role's pages.
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
        "crumb": "PORTAL / STUDENT LOGIN",
        "pill_label": "Student Portal",
        "pill_kind": "ok",
        "hero_eyebrow": "GAPLENS · STUDENT ACCESS",
        "hero_title": "Smart marks coaching for every CIA & ESE",
        "hero_text": (
            "Sign in to view your enrolled subjects, track live target scores, "
            "diagnose question-wise mistakes, and access verified revision resources."
        ),
        "cards": [
            (
                ("GOAL TRACKER &", "CIA ANALYSIS"),
                "LIVE TARGET STATUS",
                "Pinpoint silly losses, time pressure, and concept gaps on every paper.",
                components.ICON_TARGET,
                "#43A854",
            ),
            (
                ("WEAK TOPICS &", "ESE FEEDBACK"),
                "CURATED RESOURCES",
                "Revise top weak topics with verified links and published faculty reviews.",
                components.ICON_BOOK,
                "#F27D65",
            ),
        ],
        "head_cls": "gl-login-head-student",
        "badge_cls": "gl-login-badge-student",
        "icon": ICON_STUDENT,
        "form_desc": "Enter your student username and password to open your dashboard.",
        "placeholder_user": "student",
        "access_note": "<b>Student access:</b> Opens My Subjects and Subject Dashboard only.",
    },
    "Faculty": {
        "crumb": "PORTAL / FACULTY LOGIN",
        "pill_label": "Faculty Portal",
        "pill_kind": "coral",
        "hero_eyebrow": "GAPLENS · FACULTY ACCESS",
        "hero_title": "Manage subjects, papers & class-wide insights",
        "hero_text": (
            "Sign in to create courses, define question papers, upload CIA & ESE marks, "
            "publish presentation feedback, and monitor early-warning alerts."
        ),
        "cards": [
            (
                ("SUBJECTS,", "PAPERS & MARKS"),
                "COURSE PLANS + CSV",
                "Map questions to syllabus topics and record class marks in seconds.",
                components.ICON_BARS,
                "#F27D65",
            ),
            (
                ("ESE SCRIPTS &", "CLASS INSIGHTS"),
                "HEATMAPS & ALERTS",
                "Draft answer-script feedback and spot topics the class needs to revise.",
                components.ICON_TREND_UP,
                "#43A854",
            ),
        ],
        "head_cls": "gl-login-head-faculty",
        "badge_cls": "gl-login-badge-faculty",
        "icon": ICON_FACULTY,
        "form_desc": "Enter your faculty admin username and password to open the Faculty portal.",
        "placeholder_user": "admin",
        "access_note": (
            "<b>Faculty access:</b> Opens Subjects, Papers &amp; Marks, ESE Scripts, "
            "Resources, and Class Insights."
        ),
    },
}


def _on_login_tab_change() -> None:
    chosen = st.session_state.get(LOGIN_TAB_KEY)
    if chosen in TAB_TO_ROLE:
        st.session_state[LOGIN_ROLE_KEY] = TAB_TO_ROLE[chosen]


def render_login() -> None:
    """Render the GapLens login screen with top Student / Faculty login selector."""
    theme.hide_sidebar()

    role = st.session_state.get(LOGIN_ROLE_KEY, "Student")
    if role not in config.ROLES:
        role = "Student"
        st.session_state[LOGIN_ROLE_KEY] = role

    # ===================== 1. TOP WHITE HEADER BAR =====================
    with st.container(key="login_topbar"):
        tb_brand, tb_switch = st.columns([2.1, 1.5], gap="medium", vertical_alignment="center")
        with tb_brand:
            components.render(
                f'<div class="gl-topbar-left">'
                f'{components.home_topbar_brand()}'
                f'<span class="gl-meta" style="margin-left:6px">{config.APP_TAGLINE}</span>'
                f'</div>'
            )
        with tb_switch:
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

    copy = PORTAL_COPY[role]

    # ===================== 2. BREADCRUMB & PORTAL CHIPS =====================
    chips = (
        components.pill("CHRIST University", "gold")
        + components.pill(copy["pill_label"], copy["pill_kind"])
    )
    components.render(components.home_breadcrumb(f"{role} Login", copy["crumb"], chips))

    # ===================== 3. OVERVIEW + SIGN-IN CARD =====================
    left, right = st.columns([1.12, 1.0], gap="large")

    with left:
        components.render(components.hero_banner(
            copy["hero_title"],
            copy["hero_text"],
            eyebrow=copy["hero_eyebrow"],
        ))
        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
        mini_html = "".join(
            components.home_mini_card(lines, metric, sub, icon, accent)
            for lines, metric, sub, icon, accent in copy["cards"]
        )
        components.render(f'<div class="gl-mini-stack">{mini_html}</div>')

    with right:
        with st.container(border=True, key="card_login"):
            components.render(
                f'<div class="gl-login-head {copy["head_cls"]}">'
                f'<div>'
                f'<div class="gl-login-eyebrow">ROLE-RESTRICTED SIGN IN</div>'
                f'<div class="gl-login-title">{role} Login</div>'
                f'</div>'
                f'<div class="gl-login-badge {copy["badge_cls"]}">{copy["icon"]}</div>'
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
                                f"Switch to {other} Login at the top."
                            )
                        else:
                            st.error(f"Invalid {role.lower()} username or password.")

                components.render(f'<div class="gl-login-note">{copy["access_note"]}</div>')

    components.render(
        f'<div class="gl-login-footer">{config.APP_NAME} &middot; {config.APP_TAGLINE} &middot; 2026</div>'
    )
