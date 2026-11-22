"""Faculty: My Subjects (create subjects manually, manage topics, see enrolled students)."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

import config
from core import db, subject_rules
from ui import components, profile
from ui.flash import flash

faculty = profile.current_faculty()
if faculty is None:
    components.render(components.page_header("My subjects"))
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()

dv = st.session_state.get("data_version", 0)
summaries = db.list_subject_summaries(faculty["id"])

components.render(components.page_header(
    "My subjects",
    "Subjects you teach this semester, and their topics.",
    components.pill(f'{len(summaries)} subject{"s" if len(summaries) != 1 else ""}', "gold")))

# --- subject list -----------------------------------------------------------
SEL_KEY = "fac_selected_subject"
if st.session_state.get(SEL_KEY) not in {s["id"] for s in summaries}:
    st.session_state[SEL_KEY] = summaries[0]["id"] if summaries else None


def _select(subject_id: int) -> None:
    st.session_state[SEL_KEY] = subject_id


if not summaries:
    st.info("You have no subjects yet. Create one below.")
cols = st.columns(2, gap="medium")
for i, s in enumerate(summaries):
    with cols[i % 2]:
        with components.card(f"fsubj_{s['id']}"):
            selected = s["id"] == st.session_state[SEL_KEY]
            pills = (components.pill(f'{s["class_name"]} · {s["student_count"]} students', "gold")
                     + components.pill(f'{s["topic_count"]} topics', "stretch")
                     + components.pill(f'CIA {round(s["cia_weight"] * 100)}%', "gold"))
            components.render(
                f'<div style="font-size:18px;font-weight:700">{escape(s["code"])} '
                f'{escape(s["name"])}</div><div style="margin-top:8px">{pills}</div>')
            st.button("Managing" if selected else "Manage", key=f"manage_{s['id']}",
                      type="secondary", disabled=selected, on_click=_select, args=(s["id"],),
                      icon=":material/arrow_forward:", icon_position="right")

# --- create subject + manage -------------------------------------------------
left, right = st.columns([1, 1], gap="medium")

with left, components.card("create_subject"):
    components.render('<h3 style="margin:0 0 4px">Create subject</h3>')
    tab_plan, tab_manual = st.tabs(["From course plan (Gemini)", "Manually"])
    with tab_plan:
        st.info("Course-plan upload with Gemini arrives in SAN-128. "
                "Use the Manually tab for now.")
    with tab_manual:
        cv = st.session_state.get("create_version", 0)
        default_class = summaries[-1]["class_name"] if summaries else "MCA-A"
        with st.form(f"create_subject_form_{dv}_{cv}", border=False):
            c1, c2, c3 = st.columns([1, 2, 1])
            code = c1.text_input("Code", placeholder="MCA234")
            name = c2.text_input("Name", placeholder="Computer Networks")
            class_name = c3.text_input("Class", value=default_class)
            cia_pct = st.number_input("CIA weight (%)", min_value=0, max_value=100,
                                      value=int(config.DEFAULT_CIA_WEIGHT * 100), step=5)
            topics_text = st.text_area(
                "Topics (one per line)", height=160,
                placeholder="1 | OSI and TCP/IP\n1 | Routing\n2 | Transport layer",
                help="Start a line with a unit number and a bar, like '2 | Stacks'. "
                     "Lines without one join the previous unit.")
            submitted = st.form_submit_button("Create subject", type="primary",
                                              icon=":material/add_task:")
        if submitted:
            topics = subject_rules.parse_topic_lines(topics_text)
            errors = subject_rules.validate_subject(code, name, class_name, cia_pct, topics)
            new_id = None
            if not errors:
                try:
                    new_id = db.create_subject_with_topics(
                        faculty["id"], code, name, class_name, cia_pct / 100, topics)
                except ValueError as exc:  # includes db.DuplicateError
                    errors.append(str(exc))
            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.session_state[SEL_KEY] = new_id
                st.session_state["create_version"] = cv + 1
                flash(f"Created {code.strip().upper()} with {len(topics)} topics. "
                      f"Students in {class_name.strip()} can now enroll.")
                st.rerun()
        st.caption(f"ESE weight is the rest · pass mark {config.ESE_PASS_MARK} in ESE.")

with right, components.card("manage_subject"):
    sid = st.session_state[SEL_KEY]
    subject = next((s for s in summaries if s["id"] == sid), None)
    if subject is None:
        components.render('<h3 style="margin:0">Topics</h3>')
        st.caption("Create a subject to manage its topics.")
    else:
        components.render(
            f'<h3 style="margin:0 0 4px">Topics · {escape(subject["code"])}</h3>'
            f'<p class="gl-subtitle">Add, rename or remove topics. '
            f'Questions tagged with a removed topic become untagged.</p>')
        tv = st.session_state.get("topics_version", 0)
        topics = db.list_topics(sid)
        base = pd.DataFrame(
            [{"id": t["id"], "unit_no": t["unit_no"], "title": t["title"]} for t in topics],
            columns=["id", "unit_no", "title"]).astype({"id": "Int64", "unit_no": "Int64"})
        edited = st.data_editor(
            base, key=f"topics_{dv}_{tv}_{sid}", num_rows="dynamic", hide_index=True,
            column_order=("unit_no", "title"),
            column_config={
                "unit_no": st.column_config.NumberColumn("Unit", min_value=1, step=1, format="%d"),
                "title": st.column_config.TextColumn("Topic", required=True)})

        def save_topics() -> None:
            rows = [{"id": None if pd.isna(r["id"]) else int(r["id"]),
                     "unit_no": None if pd.isna(r["unit_no"]) else int(r["unit_no"]),
                     "title": "" if pd.isna(r["title"]) else str(r["title"])}
                    for _, r in edited.iterrows()]
            errors = subject_rules.validate_topic_rows(rows)
            if not rows:
                errors.append("A subject needs at least one topic.")
            if errors:
                st.session_state["_topic_errors"] = errors
                return
            db.update_topics(sid, rows)
            st.session_state["topics_version"] = tv + 1
            flash(f'Topics for {subject["code"]} saved.')

        st.button("Save topics", key="save_topics", type="primary", on_click=save_topics,
                  icon=":material/save:")
        for e in st.session_state.pop("_topic_errors", []):
            st.error(e)

        components.render('<h3 style="margin:18px 0 4px">Enrolled students</h3>')
        enrolled = db.list_subject_enrollments(sid)
        if enrolled:
            st.dataframe(pd.DataFrame(
                {"Roll no": [e["roll_no"] for e in enrolled],
                 "Name": [e["name"] for e in enrolled],
                 "Target": [e["target"] for e in enrolled]}),
                hide_index=True,
                column_config={"Target": st.column_config.NumberColumn(format="%g")})
        else:
            st.caption("No students have enrolled yet.")
