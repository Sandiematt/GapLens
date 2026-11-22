"""Faculty: My Subjects (create subjects manually, manage topics, see enrolled students)."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

import config
from core import db, gemini_client, subject_rules
from ui import components, profile, secrets
from ui.flash import flash

PLAN_KEY = "course_plan_parsed"  # the parsed course plan awaiting review

faculty = profile.current_faculty()
if faculty is None:
    components.render(components.page_header("My subjects"))
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()

data_version = st.session_state.get("data_version", 0)
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
with st.container(key="fsubj_list"):
    cols = st.columns(2, gap="medium")
    for i, s in enumerate(summaries):
        with cols[i % 2], components.card(f"fsubj_{s['id']}"):
            selected = s["id"] == st.session_state[SEL_KEY]
            pills = (components.pill(f'{s["class_name"]} · {s["student_count"]} students', "gold")
                     + components.pill(f'{s["topic_count"]} topics', "stretch")
                     + components.pill(f'CIA {round(s["cia_weight"] * 100)}%', "gold"))
            components.render(components.faculty_subject_summary(s["code"], s["name"], pills))
            st.button("Managing" if selected else "Manage", key=f"manage_{s['id']}",
                      type="secondary", disabled=selected, on_click=_select, args=(s["id"],),
                      icon=":material/arrow_forward:", icon_position="right")


def create_subject(code: str, name: str, class_name: str, cia_pct: float,
                   topics: list[tuple[int, str]], errors: list[str], source: str = "") -> bool:
    """Validate and create a subject (both tabs). Shows errors; flashes and returns True on success."""
    errors = list(errors)
    errors += [e for e in subject_rules.validate_subject(code, name, class_name, cia_pct, topics)
               if e not in errors]
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
        return False
    st.session_state[SEL_KEY] = new_id
    flash(f"Created {code.strip().upper()} with {len(topics)} topics{source}. "
          f"Students in {class_name.strip()} can now enroll.")
    return True


def ese_rest_caption() -> None:
    st.caption(f"ESE weight is the rest · pass mark {config.ESE_PASS_MARK} in ESE.")


def plan_tab(default_class: str) -> None:
    gemini_key = secrets.get_gemini_key()
    plan_version = st.session_state.get("plan_version", 0)
    parsed = st.session_state.get(PLAN_KEY)
    if not gemini_key:
        st.info("No Gemini API key is configured, so course-plan parsing is off. "
                "Create the subject on the **Manually** tab, or add `GEMINI_API_KEY` to "
                "`.streamlit/secrets.toml` (see `secrets.toml.example`) and restart the app.")
    if parsed is None:
        plan_file = st.file_uploader(
            "Course plan (PDF or image)", type=["pdf", "png", "jpg", "jpeg"],
            key=f"plan_up_{plan_version}",
            help="Gemini reads the subject code, name, units and topics. "
                 "You review everything before the subject is created.")
        if st.button("Parse with Gemini", key="plan_parse", type="primary",
                     icon=":material/auto_awesome:",
                     disabled=not gemini_key or plan_file is None):
            with st.spinner("Reading the course plan with Gemini…"):
                try:
                    result = gemini_client.parse_course_plan(
                        plan_file.getvalue(),
                        gemini_client.guess_mime(plan_file.name, plan_file.type),
                        gemini_key, secrets.get_gemini_model())
                except gemini_client.GeminiError as exc:
                    st.error(f"{exc} You can still create the subject manually.")
                else:
                    st.session_state[PLAN_KEY] = {"file": plan_file.name, **result}
                    st.rerun()
        st.caption("Gemini's free tier may use uploaded files to improve Google's products.")
        return

    n_topics = sum(len(u["topics"]) for u in parsed["units"])
    file_col, replace_col = st.columns([5, 1], vertical_alignment="center")
    with file_col:
        components.render(components.file_summary(
            parsed["file"], f'{len(parsed["units"])} units found · {n_topics} topics · '
                            "edit below before saving"))

    def _discard_plan() -> None:
        st.session_state.pop(PLAN_KEY, None)
        st.session_state["plan_version"] = plan_version + 1

    replace_col.button("Replace", key="plan_replace", on_click=_discard_plan, type="tertiary")
    plan_rows = pd.DataFrame(
        [{"unit_no": u["unit_no"], "unit_title": u["title"], "topic": t}
         for u in parsed["units"] for t in u["topics"]],
        columns=["unit_no", "unit_title", "topic"]).astype({"unit_no": "Int64"})
    with st.form(f"plan_form_{data_version}_{plan_version}", border=False):
        c1, c2, c3 = st.columns([1, 2, 1])
        code = c1.text_input("Code", value=parsed["subject_code"], key=f"plan_code_{plan_version}")
        name = c2.text_input("Name", value=parsed["subject_name"], key=f"plan_name_{plan_version}")
        class_name = c3.text_input("Class", value=default_class, key=f"plan_class_{plan_version}")
        cia_pct = st.number_input("CIA weight (%)", min_value=0, max_value=100,
                                  value=int(config.DEFAULT_CIA_WEIGHT * 100), step=5,
                                  key=f"plan_cia_{plan_version}")
        plan_edit = st.data_editor(
            plan_rows, key=f"plan_rows_{data_version}_{plan_version}", num_rows="dynamic",
            hide_index=True,
            column_config={
                "unit_no": st.column_config.NumberColumn("Unit", min_value=1, step=1,
                                                         format="%d", width="small"),
                "unit_title": st.column_config.TextColumn("Unit title"),
                "topic": st.column_config.TextColumn("Topic", required=True)})
        submitted = st.form_submit_button("Create subject", type="primary",
                                          icon=":material/add_task:")
    ese_rest_caption()
    if submitted:
        rows = [{"unit_no": None if pd.isna(r["unit_no"]) else int(r["unit_no"]),
                 "title": "" if pd.isna(r["topic"]) else str(r["topic"]).strip()}
                for _, r in plan_edit.iterrows()
                if not all(pd.isna(r[c]) or str(r[c]).strip() == "" for c in plan_edit.columns)]
        topics = [(r["unit_no"], r["title"]) for r in rows]
        if create_subject(code, name, class_name, cia_pct, topics,
                          subject_rules.validate_topic_rows(rows), " from the course plan"):
            st.session_state.pop(PLAN_KEY, None)
            st.session_state["plan_version"] = plan_version + 1
            st.rerun()


def manual_tab(default_class: str) -> None:
    create_version = st.session_state.get("create_version", 0)
    with st.form(f"create_subject_form_{data_version}_{create_version}", border=False):
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
    if submitted and create_subject(code, name, class_name, cia_pct,
                                    subject_rules.parse_topic_lines(topics_text), []):
        st.session_state["create_version"] = create_version + 1
        st.rerun()
    ese_rest_caption()


# --- create subject + manage -------------------------------------------------
left, right = st.columns([1, 1], gap="medium")

with left, components.card("create_subject"):
    components.render(components.card_title("Create subject"))
    tab_plan, tab_manual = st.tabs(["From course plan (Gemini)", "Manually"])
    default_class = summaries[-1]["class_name"] if summaries else config.DEMO_CLASS
    with tab_plan:
        plan_tab(default_class)
    with tab_manual:
        manual_tab(default_class)

sid = st.session_state[SEL_KEY]
subject = next((s for s in summaries if s["id"] == sid), None)
with right, components.card("manage_subject"):
    if subject is None:
        components.render(components.card_title("Topics", "Create a subject to manage its topics."))
    else:
        components.render(components.card_title(
            f'Topics · {subject["code"]}',
            "Add, rename or remove topics. Questions tagged with a removed topic become untagged."))
        topics_version = st.session_state.get("topics_version", 0)
        topics = db.list_topics(sid)
        base = pd.DataFrame(
            [{"id": t["id"], "unit_no": t["unit_no"], "title": t["title"]} for t in topics],
            columns=["id", "unit_no", "title"]).astype({"id": "Int64", "unit_no": "Int64"})
        edited = st.data_editor(
            base, key=f"topics_{data_version}_{topics_version}_{sid}", num_rows="dynamic",
            hide_index=True, column_order=("unit_no", "title"), height=320,
            column_config={
                "unit_no": st.column_config.NumberColumn("Unit", min_value=1, step=1, format="%d",
                                                         alignment="right", width="small"),
                "title": st.column_config.TextColumn("Topic", required=True)})

        def save_topics() -> None:
            rows = [{"id": None if pd.isna(r["id"]) else int(r["id"]),
                     "unit_no": None if pd.isna(r["unit_no"]) else int(r["unit_no"]),
                     "title": "" if pd.isna(r["title"]) else str(r["title"])}
                    for _, r in edited.iterrows()]
            errors = subject_rules.validate_topic_rows(rows)
            if errors:
                st.session_state["_topic_errors"] = errors
                return
            db.update_topics(sid, rows)
            st.session_state["topics_version"] = topics_version + 1
            flash(f'Topics for {subject["code"]} saved.')

        st.button("Save topics", key="save_topics", type="primary", on_click=save_topics,
                  icon=":material/save:")
        for e in st.session_state.pop("_topic_errors", []):
            st.error(e)

# Full width below both columns, so the two cards above stay a similar height.
if subject is not None:
    with components.card("enrolled_students"):
        enrolled = db.list_subject_enrollments(sid)
        components.render(components.card_title(
            f'Enrolled students · {subject["code"]}',
            f'{len(enrolled)} student{"s" if len(enrolled) != 1 else ""} with the target each one set.'))
        if enrolled:
            components.render(components.table(
                ["Roll no", "Name", "Target"],
                [[escape(e["roll_no"]), escape(e["name"]),
                  "&ndash;" if e["target"] is None else components.num(e["target"])]
                 for e in enrolled], numeric=(2,), scroll=True))
        else:
            st.caption("No students have enrolled yet.")
