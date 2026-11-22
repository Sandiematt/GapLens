"""Sidebar: brand, role navigation, View-as switch, profile picker, demo reset."""
from __future__ import annotations

import streamlit as st

import config
from core import db
from ui import components, profile
from ui.flash import flash

LOGO_SVG = ('<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" '
            'stroke-linecap="round" stroke-linejoin="round" width="22" height="22">'
            '<circle cx="12" cy="12" r="10"/><line x1="14.31" y1="8" x2="20.05" y2="17.94"/>'
            '<line x1="9.69" y1="8" x2="21.17" y2="8"/><line x1="7.38" y1="12" x2="13.12" y2="2.06"/>'
            '<line x1="9.69" y1="16" x2="3.95" y2="6.06"/><line x1="14.31" y1="16" x2="2.83" y2="16"/>'
            '<line x1="16.62" y1="12" x2="10.88" y2="21.94"/></svg>')


def _brand() -> None:
    components.render(
        f'<div class="gl-brand"><div class="gl-brand-badge">{LOGO_SVG}</div><div>'
        f'<div class="gl-brand-name">{config.APP_NAME}</div>'
        f'<div class="gl-brand-tag">{config.APP_TAGLINE}</div></div></div>')


def _on_role_change() -> None:
    chosen = st.session_state.get("role_widget")
    if chosen:  # ignore a deselect click
        profile.set_role(chosen)


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
            profile.reset_demo_data()
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
            components.render(components.label("View as"))
            st.session_state["role_widget"] = role  # sync before the widget renders
            st.segmented_control("View as", list(config.ROLES), key="role_widget", width="stretch",
                                 label_visibility="collapsed", on_change=_on_role_change)
            _profile_picker(role)
            _create_profile_form(role)
            if role == "Faculty":
                _reset_control()
