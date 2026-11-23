"""Role, authentication, and profile state.

Session keys:
  authenticated bool — whether the user has signed in
  auth_username username used at sign-in
  active_role   "Student" | "Faculty"
  student_id    id of the active student profile
  faculty_id    id of the active faculty profile
Stale ids (e.g. after a data reset) silently fall back to the defaults.
"""
from __future__ import annotations

import hmac

import streamlit as st

import config
from core import db, seed

AUTH_KEY, AUTH_USER_KEY = "authenticated", "auth_username"
ROLE_KEY, STUDENT_KEY, FACULTY_KEY = "active_role", "student_id", "faculty_id"


def ensure_state() -> None:
    st.session_state.setdefault(ROLE_KEY, config.ROLES[0])


def is_authenticated() -> bool:
    return bool(st.session_state.get(AUTH_KEY)) and st.session_state.get(ROLE_KEY) in config.ROLES


def authenticate(role: str, username: str, password: str) -> bool:
    """Return True iff ``username`` and ``password`` match ``role``'s credentials."""
    expected = config.LOGIN_CREDENTIALS.get(role)
    if expected is None:
        return False
    exp_user, exp_pass = expected
    return (
        hmac.compare_digest(username.strip().lower(), exp_user.lower())
        and hmac.compare_digest(password, exp_pass)
    )


def matching_role(username: str, password: str) -> str | None:
    """Return the role matching these credentials, if any."""
    for role in config.ROLES:
        if authenticate(role, username, password):
            return role
    return None


def login(role: str, username: str) -> None:
    """Mark the session authenticated for ``role``."""
    if role not in config.ROLES:
        raise ValueError(f"Unknown role: {role}")
    st.session_state[AUTH_KEY] = True
    st.session_state[ROLE_KEY] = role
    st.session_state[AUTH_USER_KEY] = username.strip()


def logout() -> None:
    """Clear authentication state so the app returns to the login screen."""
    for key in (AUTH_KEY, AUTH_USER_KEY, ROLE_KEY, "confirm_reset"):
        st.session_state.pop(key, None)


def auth_username() -> str:
    return str(st.session_state.get(AUTH_USER_KEY) or "")


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


SUBJECT_KEY = "selected_subject_id"


def enrolled_subjects(student: dict | None) -> list[dict]:
    """Subjects the student is enrolled in (subject dicts plus ``target``)."""
    if not student:
        return []
    targets = {e["subject_id"]: e["target"] for e in db.list_enrollments(student["id"])}
    return [dict(s, target=targets[s["id"]])
            for s in db.list_subjects(class_name=student["class_name"]) if s["id"] in targets]


def current_subject(student: dict | None) -> dict | None:
    """The chosen enrolled subject (session state), defaulting to the first."""
    subjects = enrolled_subjects(student)
    if not subjects:
        st.session_state[SUBJECT_KEY] = None
        return None
    chosen = next((s for s in subjects if s["id"] == st.session_state.get(SUBJECT_KEY)), subjects[0])
    st.session_state[SUBJECT_KEY] = chosen["id"]
    return chosen


def select_subject(subject_id: int) -> None:
    st.session_state[SUBJECT_KEY] = subject_id


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
    st.session_state.pop(SUBJECT_KEY, None)
    # Widget keys that cache DB values include this counter, so they refresh.
    st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
