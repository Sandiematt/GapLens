"""Student: My Subjects (enroll and set a target)."""
from __future__ import annotations

from html import escape

import streamlit as st

import config
from core import db
from ui import components, profile, theme
from ui.flash import flash

student = profile.current_student()
if student is None:
    components.render(components.page_header("My subjects"))
    st.info("No student profile exists yet. Create one from the sidebar.")
    st.stop()

subjects = db.list_subjects(class_name=student["class_name"])
enrollments = {e["subject_id"]: e for e in db.list_enrollments(student["id"])}
enrolled_count = sum(1 for s in subjects if s["id"] in enrollments)

components.render(components.page_header(
    "My subjects",
    f'{student["class_name"]} · Enroll in a subject and set the mark you\'re aiming for.',
    components.pill(f"{enrolled_count} enrolled", "ok")
    + components.pill(f'{len(subjects)} subject{"s" if len(subjects) != 1 else ""} '
                      f'in {student["class_name"]}', "gold")))

# Banner variants alternate between the hero gold and deep gold, as in the design.
BANNERS = [
    (theme.GRAD_HERO, theme.GOLD[950], "&#128214;"),
    (theme.GRAD_DEEP, "#FFFFFF", "&lt;/&gt;"),
]
SEG_COLORS = [theme.SHADES["lemon"][1], theme.SHADES["honey"][1],
              theme.SHADES["marigold"][1], theme.SHADES["bronze"][1]]


def split_html(subject: dict) -> str:
    w = subject["cia_weight"]
    cia_pct, ese_pct = round(w * 100), round((1 - w) * 100)
    parts = " + ".join(f"{c} /{config.COMPONENTS[c]}" for c in config.CIA_COMPONENTS)
    scale = "halved" if abs(w - 0.5) < 1e-9 else f"scaled to {cia_pct}"
    flex = [config.COMPONENTS[c] * w for c in config.CIA_COMPONENTS] + [config.COMPONENTS["ESE"] * (1 - w)]
    segs = "".join(f'<div style="flex:{f};background:{c}"></div>'
                   for f, c in zip(flex, SEG_COLORS) if f > 0)
    return (f'<div><div class="gl-split-labels"><span style="color:{theme.GOLD[800]}">'
            f'CIA {cia_pct} · {parts}, {scale}</span>'
            f'<span style="color:{theme.SHADES["bronze"][2]}">ESE {ese_pct}</span></div>'
            f'<div class="gl-bar">{segs}</div></div>')


def card_html(subject: dict, idx: int, enrolled: bool, target) -> str:
    grad, fg, icon = BANNERS[idx % len(BANNERS)]
    topics = db.list_topics(subject["id"])
    chips = "".join(components.chip(t["title"], i) for i, t in enumerate(topics))
    if enrolled:
        meta = "Enrolled" + (f" · Target {target:g}" if target is not None else " · No target yet")
    else:
        meta = "Not enrolled yet"
    return components._h(
        f'<div class="gl-banner" style="background:{grad};color:{fg}"><div>'
        f'<div class="gl-banner-code" style="opacity:.9">{escape(subject["code"])} · {escape(subject["class_name"])}</div>'
        f'<div class="gl-banner-name">{escape(subject["name"])}</div></div>'
        f'<div class="gl-banner-icon" style="color:{theme.GOLD[700]}">{icon}</div></div>'
        f'<div class="gl-card-body"><div class="gl-row"><div style="display:flex;align-items:center;gap:10px">'
        f'<div class="gl-fac-avatar">{escape(components.initials(subject["faculty_name"]))}</div><div>'
        f'<div class="gl-meta">Faculty</div><div style="font-size:14px;font-weight:600">'
        f'{escape(subject["faculty_name"])}</div></div></div><span class="gl-meta">{escape(meta)}</span></div>'
        f'{split_html(subject)}<div class="gl-topics">{chips}</div></div>')


def parse_target(raw) -> float | None:
    return None if raw is None else float(raw)


def do_enroll(subject_id: int, name: str, key: str) -> None:
    try:
        db.enroll(student["id"], subject_id, parse_target(st.session_state.get(key)))
    except ValueError as exc:
        st.session_state["_subject_error"] = str(exc)
        return
    flash(f"Enrolled in {name}.")


def do_save(subject_id: int, name: str, key: str) -> None:
    raw = st.session_state.get(key)
    if raw is None:
        st.session_state["_subject_error"] = "Enter a target between 0 and 100 first."
        return
    try:
        db.set_target(student["id"], subject_id, float(raw))
    except ValueError as exc:
        st.session_state["_subject_error"] = str(exc)
        return
    flash(f"Target for {name} saved: {float(raw):g}.")


if err := st.session_state.pop("_subject_error", None):
    st.error(err)

if not subjects:
    st.info(f'No subjects have been created for {student["class_name"]} yet.')

cols = st.columns(2, gap="medium")
for idx, subject in enumerate(subjects):
    enrollment = enrollments.get(subject["id"])
    enrolled = enrollment is not None
    target = enrollment["target"] if enrolled else None
    sid = subject["id"]
    with cols[idx % 2]:
        with st.container(key=f"subjcard_{sid}"):
            components.render(card_html(subject, idx, enrolled, target))
            with st.container(key=f"subjact_{sid}"):
                tkey = f"target_{st.session_state.get('data_version', 0)}_{student['id']}_{sid}"
                if tkey not in st.session_state:
                    st.session_state[tkey] = None if target is None else int(target)
                if enrolled:
                    c_in, c_save, c_state, c_open = st.columns(
                        [1.6, 0.9, 1.2, 1.5], gap="small", vertical_alignment="bottom")
                else:
                    c_in, c_btn = st.columns([2, 2], gap="small", vertical_alignment="bottom")
                c_in.number_input("Target mark (/100)", min_value=config.TARGET_MIN,
                                  max_value=config.TARGET_MAX, step=1, key=tkey,
                                  placeholder="e.g. 75")
                if enrolled:
                    c_save.button("Save", key=f"save_{sid}", on_click=do_save,
                                  args=(sid, subject["name"], tkey))
                    c_state.button("Enrolled", key=f"enrolled_{sid}", disabled=True)
                    if c_open.button("Dashboard", key=f"open_{sid}",
                                     icon=":material/arrow_forward:", icon_position="right"):
                        st.switch_page("views/student_dashboard.py")
                else:
                    c_btn.button("Enroll", key=f"enroll_{sid}", type="primary",
                                 icon=":material/add:", on_click=do_enroll,
                                 args=(sid, subject["name"], tkey))

components.render(components.callout(
    "Your target drives the status on each subject dashboard. "
    "You can change it any time before the ESE results are published."))
