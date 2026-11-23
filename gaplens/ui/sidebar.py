"""Sidebar: brand, role navigation, signed-in badge, profile picker, logout, demo reset."""
from __future__ import annotations

from html import escape

import streamlit as st

import config
from core import db
from ui import components, loader, profile
from ui.flash import flash

LOGO_SVG = ('<svg viewBox="0 0 36 36" width="36" height="36" fill="none">'
            '<circle cx="18" cy="18" r="17" fill="#1D1F28"/>'
            '<path d="M18 1 A17 17 0 0 1 18 35 Z" fill="#F27D65"/>'
            '<circle cx="18" cy="18" r="11" fill="#262833"/>'
            '<text x="18" y="23" text-anchor="middle" fill="#F27D65" '
            'font-family="Barlow Condensed, sans-serif" font-weight="700" font-size="16">G</text>'
            '</svg>')


def _brand() -> None:
    components.render(
        f'<div class="gl-brand"><div class="gl-brand-badge">{LOGO_SVG}</div><div>'
        f'<div class="gl-brand-name">{config.APP_NAME}</div>'
        f'<div class="gl-brand-tag">{config.APP_TAGLINE}</div></div></div>')


def _signed_in_badge(role: str) -> None:
    dot_color = "#8FE089" if role == "Student" else "#F27D65"
    user = profile.auth_username()
    user_html = f'<span class="gl-role-user">@{escape(user)}</span>' if user else ""
    components.render(
        f'<div class="gl-role-badge">'
        f'<span class="gl-role-badge-text">'
        f'<span class="gl-role-dot" style="background:{dot_color}"></span>{escape(role)}'
        f'</span>{user_html}</div>'
    )


def _logout_control() -> None:
    if st.button("Log out", key="logout_btn", icon=":material/logout:", width="stretch"):
        profile.logout()
        flash("Signed out successfully.")
        st.rerun()


def _on_profile_change(role: str) -> None:
    chosen = st.session_state.get(f"profile_widget_{role}")
    if chosen is not None:
        (profile.select_student if role == "Student" else profile.select_faculty)(chosen)


def student_option_label(student: dict) -> str:
    """Student picker label: roll number and class only, never another student's name."""
    return f'{student["roll_no"]} · {student["class_name"]}'


def _profile_picker(role: str) -> None:
    if role == "Student":
        people = db.list_students()
        active = profile.current_student()
        label = student_option_label
    else:
        people = db.list_faculty()
        active = profile.current_faculty()
        label = lambda p: p["name"]  # noqa: E731
    if not people or active is None:
        st.caption("No profiles yet. Create one below.")
        return
    ids = [p["id"] for p in people]
    by_id = {p["id"]: p for p in people}
    key = f"profile_widget_{role}"
    st.session_state[key] = active["id"]  # sync before the widget renders
    st.selectbox("Profile", ids, key=key, format_func=lambda i: label(by_id[i]),
                 label_visibility="collapsed", on_change=_on_profile_change, args=(role,))
    sub = f'{active["roll_no"]} · {active["class_name"]}' if role == "Student" else "Faculty"
    components.render(components.profile_chip(active["name"], sub))


def _on_subject_change() -> None:
    chosen = st.session_state.get("subject_widget")
    if chosen is not None:
        profile.select_subject(chosen)


def _subject_picker() -> None:
    """Sidebar 'Subject' select over the student's enrolled subjects."""
    subjects = profile.enrolled_subjects(profile.current_student())
    components.render(components.label("Subject", "gl-label-gap"))
    if not subjects:
        st.caption("Enroll in a subject from My Subjects.")
        return
    current = profile.current_subject(profile.current_student())
    by_id = {s["id"]: s for s in subjects}
    st.session_state["subject_widget"] = current["id"]  # sync before the widget renders
    st.selectbox("Subject", list(by_id), key="subject_widget",
                 format_func=lambda i: f'{by_id[i]["code"]} {by_id[i]["name"]}',
                 label_visibility="collapsed", on_change=_on_subject_change)


def _create_profile_form(role: str) -> None:
    with st.expander("Create new profile"):
        with st.form(f"create_profile_{role}", clear_on_submit=False):
            if role == "Student":
                roll = st.text_input("Roll number", placeholder="e.g. 25MCA041")
                name = st.text_input("Name")
                class_name = st.text_input("Class", value=config.DEMO_CLASS)
            else:
                name = st.text_input("Name", placeholder="e.g. Dr. Jane Doe")
            submitted = st.form_submit_button("Create profile", type="primary")
        if not submitted:
            return
        try:
            if role == "Student":
                created = profile.create_student(roll, name, class_name)
                flash(f'Created profile for {created["name"]} ({created["roll_no"]}).')
            else:
                created = profile.create_faculty(name)
                flash(f'Created faculty profile {created["name"]}.')
        except db.DuplicateError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.rerun()


def _reset_control() -> None:
    if st.session_state.get("confirm_reset"):
        st.warning("This wipes all data and restores the demo. Continue?")
        yes, no = st.columns(2)
        if yes.button("Yes, reset", key="reset_yes", type="primary"):
            loader.run_with_loading_bar(
                "Resetting Demo Data",
                "Restoring seeded subjects, marks & reviews…",
                profile.reset_demo_data,
                done_status="Demo data restored.",
            )
            st.session_state["confirm_reset"] = False
            flash("Demo data restored.")
            st.rerun()
        if no.button("Cancel", key="reset_no"):
            st.session_state["confirm_reset"] = False
            st.rerun()
    elif st.button("Reset demo data", key="reset_start"):
        st.session_state["confirm_reset"] = True
        st.rerun()


def render_sidebar(pages: list, role: str) -> None:
    """Draw the whole sidebar. ``pages`` are the st.Page objects for ``role``."""
    with st.sidebar:
        _brand()
        components.render(components.label(role, "gl-label-gap"))
        for page in pages:
            st.page_link(page)
        if role == "Student":
            _subject_picker()
        with st.container(key="sidebar_footer"):
            components.render(components.label("Signed in as"))
            _signed_in_badge(role)
            _profile_picker(role)
            _create_profile_form(role)
            if role == "Faculty":
                _reset_control()
            _logout_control()
        components.render('<div class="gl-side-year">GAPLENS &middot; 2026</div>')
