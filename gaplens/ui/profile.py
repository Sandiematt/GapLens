"""Role and profile state (no login: the sidebar picks who you are).

Session keys:
  active_role  "Student" | "Faculty"
  student_id   id of the active student profile
  faculty_id   id of the active faculty profile
Stale ids (e.g. after a data reset) silently fall back to the defaults.
"""
from __future__ import annotations

import streamlit as st

import config
from core import db, seed

ROLE_KEY, STUDENT_KEY, FACULTY_KEY = "active_role", "student_id", "faculty_id"


def ensure_state() -> None:
    st.session_state.setdefault(ROLE_KEY, config.ROLES[0])


def current_role() -> str:
    ensure_state()
    role = st.session_state[ROLE_KEY]
    return role if role in config.ROLES else config.ROLES[0]


def set_role(role: str) -> None:
    if role in config.ROLES:
        st.session_state[ROLE_KEY] = role


def current_student() -> dict | None:
    """Active student; falls back to the demo student, then the first student."""
    student = db.get_student(st.session_state.get(STUDENT_KEY) or -1)
    if student is None:
        student = db.get_student_by_roll(config.DEMO_STUDENT_ROLL)
        if student is None:
            students = db.list_students()
            student = students[0] if students else None
        st.session_state[STUDENT_KEY] = student["id"] if student else None
    return student


def current_faculty() -> dict | None:
    faculty = db.get_faculty(st.session_state.get(FACULTY_KEY) or -1)
    if faculty is None:
        rows = db.list_faculty()
        faculty = rows[0] if rows else None
        st.session_state[FACULTY_KEY] = faculty["id"] if faculty else None
    return faculty


def select_student(student_id: int) -> None:
    st.session_state[STUDENT_KEY] = student_id


def select_faculty(faculty_id: int) -> None:
    st.session_state[FACULTY_KEY] = faculty_id


def create_student(roll_no: str, name: str, class_name: str) -> dict:
    """Create and activate a student. Raises db.DuplicateError / ValueError."""
    student_id = db.add_student(roll_no, name, class_name)
    select_student(student_id)
    return db.get_student(student_id)


def create_faculty(name: str) -> dict:
    faculty_id = db.add_faculty(name)
    select_faculty(faculty_id)
    return db.get_faculty(faculty_id)


def reset_demo_data() -> None:
    """Restore the seeded state and drop stale profile selections."""
    seed.reset_demo()
    st.session_state.pop(STUDENT_KEY, None)
    st.session_state.pop(FACULTY_KEY, None)
    # Widget keys that cache DB values include this counter, so they refresh.
    st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
