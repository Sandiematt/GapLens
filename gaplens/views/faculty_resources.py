"""Faculty: Resources (verified links per topic, shown to students as Verified)."""
from __future__ import annotations

import streamlit as st

from core import db, suggestions
from ui import components, profile
from ui.flash import flash

faculty = profile.current_faculty()
if faculty is None:
    components.render(components.page_header("Resources"))
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()

data_version = st.session_state.get("data_version", 0)
subjects = db.list_subjects(faculty_id=faculty["id"])
components.render(components.page_header(
    "Resources", "Links students see as Verified on their weak topics."))
if not subjects:
    st.info("Create a subject first, then add resources for its topics.")
    st.stop()

labels = {s["id"]: f'{s["code"]} {s["name"]}' for s in subjects}
sid = st.selectbox("Subject", list(labels), format_func=labels.get, key=f"res_subject_{data_version}")
topics = db.list_topics(sid)
titles = {t["id"]: t["title"] for t in topics}
resources = db.list_resources(sid)
res_version = st.session_state.get("res_version", 0)

left, right = st.columns([1, 1], gap="medium")
with left, components.card("res_add"):
    components.render(components.card_title("Add a resource", labels[sid]))
    components.render('<div class="gl-rule-note">Only add links you have opened and checked '
                      '&mdash; students see these as Verified.</div>')
    with st.form(f"res_form_{data_version}_{res_version}_{sid}", border=False):
        topic_id = st.selectbox("Topic", list(titles), format_func=titles.get) if titles else None
        title = st.text_input("Title", placeholder="Recursion and the call stack, step by step")
        link = st.text_input("Link", placeholder="https://...")
        c1, c2, c3 = st.columns(3)
        rtype = c1.selectbox("Type", suggestions.RESOURCE_TYPES, format_func=str.capitalize)
        diff = c2.selectbox("Difficulty", suggestions.DIFFICULTIES, format_func=str.capitalize)
        duration = c3.text_input("Duration", placeholder="18 min")
        submitted = st.form_submit_button("Add resource", type="primary", icon=":material/add_link:")
    if submitted:
        errors = suggestions.validate_resource(title, link, topic_id, rtype, diff)
        if errors:
            for e in errors:
                st.error(e)
        else:
            db.add_resource(sid, topic_id, title, link, rtype, diff, duration)
            st.session_state["res_version"] = res_version + 1
            flash(f'Added "{title.strip()}" to {titles[topic_id]}.')
            st.rerun()


def _delete(resource_id: int, name: str) -> None:
    db.delete_resource(resource_id)
    flash(f'Deleted "{name}".')


with right, components.card("res_list"):
    n = len(resources)
    components.render(components.card_title(
        "Resources", f'{labels[sid]} · {n} resource{"s" if n != 1 else ""} students see as Verified'))
    if not resources:
        st.caption("No resources yet. Students still get auto-suggested search links.")
    for tid, name in titles.items():
        group = [r for r in resources if r["topic_id"] == tid]
        if not group:
            continue
        components.render(components.eyebrow(
            f'{name} · {len(group)} resource{"s" if len(group) != 1 else ""}'))
        for r in group:
            a, b = st.columns([8, 1], vertical_alignment="center")
            with a:
                components.render(components.resource_list([components.resource_card(r)]))
            b.button("", key=f"del_res_{r['id']}", icon=":material/delete:", on_click=_delete,
                     args=(r["id"], r["title"]), help="Delete this resource")
