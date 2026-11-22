"""Faculty: Papers & Marks (define CIA papers, enter question-wise and ESE marks)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from core import analysis, db, marks_rules as mr
from ui import components, profile
from ui.flash import flash

faculty = profile.current_faculty()
components.render(components.page_header(
    "Papers & marks", "Set up the question paper, then upload or type each student's marks."))
if faculty is None:
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()

subjects = db.list_subjects(faculty_id=faculty["id"])
if not subjects:
    st.info("You have no subjects yet. Create one on the My Subjects page first.")
    st.stop()

data_version = st.session_state.get("data_version", 0)
papers_version = st.session_state.get("papers_version", 0)  # bumped after every save


def _bump() -> None:
    st.session_state["papers_version"] = papers_version + 1


def _val(x):
    return None if pd.isna(x) else x


# --- selectors ----------------------------------------------------------------
with components.card("paper_select"):
    c1, c2, c3 = st.columns(3, gap="medium")
    subject = c1.selectbox("Subject", subjects, key=f"pm_subject_{data_version}",
                           format_func=lambda s: f'{s["code"]} {s["name"]}')
    component = c2.selectbox(
        "Component", list(config.COMPONENTS), key=f"pm_component_{data_version}",
        format_func=lambda c: f"{c} · out of {config.COMPONENTS[c]}")
    students = db.list_subject_enrollments(subject["id"])
    c3.text_input("Class", value=f'{subject["class_name"]} · {len(students)} students',
                  disabled=True)

sid, total_max = subject["id"], config.COMPONENTS[component]
ident = f"{data_version}_{papers_version}_{sid}_{component}"
is_ese = component == "ESE"
rolls = [s["roll_no"] for s in students]


def _csv_button(label: str, text: str, filename: str, key: str) -> None:
    st.download_button(label, text, file_name=filename, mime="text/csv", key=key,
                       type="secondary", icon=":material/download:")


def _show_errors(errors: list[str]) -> None:
    shown = errors[:8]
    st.error("Nothing was saved. Fix these and try again:\n\n"
             + "\n".join(f"- {e}" for e in shown)
             + (f"\n- ...and {len(errors) - 8} more" if len(errors) > 8 else ""))


# ============================ ESE ==============================================
if is_ese:
    left, right = st.columns(2, gap="medium")
    saved = {m["roll_no"]: m["score"] for m in db.list_ese_marks(sid)}
    with left, components.card("ese_file"):
        components.render(components.card_title(
            "ESE marks file", f"Download the template, fill in each total out of {total_max}, "
                              "then upload it. Saving replaces all ESE totals."))
        _csv_button("Download CSV template", mr.ese_template_csv(rolls),
                    f'{subject["code"]}_ESE_{subject["class_name"]}.csv', f"dl_ese_{ident}")
        up = st.file_uploader("Upload ESE CSV", type="csv", key=f"up_ese_{ident}")
        if up is not None:
            rows, errors = mr.parse_ese_csv(up.getvalue())
            records = []
            if not errors:
                records, errors = mr.ese_table_to_records(rows)
            if errors:
                _show_errors(errors)
            else:
                db.save_ese_marks(sid, records)
                _bump()
                flash(f"Saved {len(records)} ESE totals from {up.name}.")
                st.rerun()
    with right, components.card("ese_stats"):
        scores = list(saved.values())
        components.render(components.card_title(
            "ESE totals", f"Out of {total_max}. Below {config.ESE_PASS_MARK} is a fail."))
        if scores:
            fails = sum(not analysis.passed_ese(s) for s in scores)
            components.render(components.pill_row(
                components.pill(f"{len(scores)} entered", "gold")
                + components.pill(f"{fails} below {config.ESE_PASS_MARK}", "at-risk" if fails else "ok")
                + components.pill(f"average {sum(scores) / len(scores):.1f}", "stretch")))
        else:
            st.caption("No ESE totals entered yet.")
    with components.card("ese_grid"):
        components.render(components.card_title("Review and edit ESE totals"))
        names = {s["roll_no"]: s["name"] for s in students}
        order = rolls + sorted(set(saved) - set(rolls))
        base = pd.DataFrame({
            "roll_no": order,
            "name": [names.get(r, mr.ANONYMOUS_NAME) for r in order],
            "score": pd.Series([saved.get(r) for r in order], dtype="float64")})
        edited = st.data_editor(
            base, key=f"ese_grid_{ident}", hide_index=True, num_rows="dynamic",
            column_config={
                "roll_no": st.column_config.TextColumn("Roll"),
                "name": st.column_config.TextColumn("Name", disabled=True),
                "score": st.column_config.NumberColumn(f"ESE /{total_max}", format="%g", step=0.5,
                                                       alignment="right")})
        if st.button("Save ESE totals", key="save_ese", type="primary", icon=":material/save:"):
            rows = [{"roll_no": _val(r["roll_no"]), "score": _val(r["score"])}
                    for _, r in edited.iterrows()]
            records, errors = mr.ese_table_to_records(rows)
            if errors:
                _show_errors(errors)
            else:
                db.save_ese_marks(sid, records)
                _bump()
                flash(f"Saved {len(records)} ESE totals.")
                st.rerun()
    st.stop()

# ============================ CIA ==============================================
questions = db.list_questions(sid, component)
topics = db.list_topics(sid)
topic_title = {t["id"]: t["title"] for t in topics}
topic_id = {}
for t in topics:
    topic_id.setdefault(t["title"], t["id"])

left, right = st.columns(2, gap="medium")

with left, components.card("paper_editor"):
    components.render(components.card_title(
        "Question paper", f"One row per question. Maximum marks should add up to {total_max}."))
    base = pd.DataFrame(
        [{"q_no": q["q_no"], "max_marks": q["max_marks"], "topic": topic_title.get(q["topic_id"])}
         for q in questions], columns=["q_no", "max_marks", "topic"]
    ).astype({"q_no": "Int64", "max_marks": "float64"})
    paper_edit = st.data_editor(
        base, key=f"paper_{ident}", num_rows="dynamic", hide_index=True,
        column_config={
            "q_no": st.column_config.NumberColumn("Q no", min_value=1, step=1, format="%d",
                                                  alignment="right"),
            "max_marks": st.column_config.NumberColumn("Max marks", min_value=0.5, step=0.5,
                                                       format="%g", alignment="right"),
            "topic": st.column_config.SelectboxColumn("Topic", options=list(topic_id),
                                                      width="medium")})
    paper_rows = [{"q_no": _val(r["q_no"]), "max_marks": _val(r["max_marks"]),
                   "topic_id": topic_id.get(_val(r["topic"]))}
                  for _, r in paper_edit.iterrows()]
    warning = mr.maxima_warning(paper_rows, total_max) if paper_rows else None
    if warning:
        st.warning(warning)

    if st.button("Save paper", key="save_paper", type="primary", icon=":material/save:"):
        errors = mr.validate_paper(paper_rows)
        if errors:
            for e in errors:
                st.error(e)
        else:
            clean = [{"q_no": int(r["q_no"]), "max_marks": float(r["max_marks"]),
                      "topic_id": r["topic_id"]} for r in paper_rows]
            db.save_paper(sid, component, clean)
            _bump()
            flash(f"Saved the {component} paper ({len(clean)} questions). "
                  "Marks for questions that still exist were kept."
                  + (" " + warning if warning else ""), "warning" if warning else "success")
            st.rerun()

with right, components.card("marks_file"):
    components.render(components.card_title(
        "Marks file", "Download the template with every roll number and a column per question, "
                      "fill it in, then upload it. Saving replaces all marks for this paper. "
                      "A blank cell means not attempted."))
    if not questions:
        st.info("Save the question paper first, then marks can be entered.")
    else:
        _csv_button("Download CSV template", mr.template_csv(rolls, questions),
                    f'{subject["code"]}_{component.replace("-", "")}_{subject["class_name"]}.csv',
                    f"dl_{ident}")
        up = st.file_uploader("Upload marks CSV", type="csv", key=f"up_{ident}")
        if up is not None:
            rows, errors = mr.parse_marks_csv(up.getvalue(), questions)
            records = []
            if not errors:
                records, errors = mr.table_to_records(rows, questions)
            if errors:
                _show_errors(errors)
            else:
                db.save_marks(sid, component, records)
                _bump()
                flash(f"Saved marks for {len({r[1] for r in records})} students from {up.name}.")
                st.rerun()

if questions:
    with components.card("marks_grid"):
        components.render(components.card_title(
            "Review and edit marks", "Leave a cell empty for not attempted. Rows empty in every "
                                     "cell are not saved. Roll numbers outside the class stay as "
                                     "anonymous rows."))
        grid = mr.marks_grid(students, questions, db.list_marks(sid, component))
        cols = [mr.qcol(q["q_no"]) for q in questions]
        base = pd.DataFrame(grid, columns=["roll_no", "name", *cols])
        base[cols] = base[cols].astype("float64")
        config_cols = {
            "roll_no": st.column_config.TextColumn("Roll"),
            "name": st.column_config.TextColumn("Name", disabled=True)}
        for q in questions:
            config_cols[mr.qcol(q["q_no"])] = st.column_config.NumberColumn(
                f'{mr.qcol(q["q_no"])} /{q["max_marks"]:g}', format="%g", step=0.5,
                alignment="right")
        edited = st.data_editor(base, key=f"grid_{ident}", hide_index=True, num_rows="dynamic",
                                column_config=config_cols)
        st.caption(f"{len(base)} rows · scores must be between 0 and each question's maximum.")
        if st.button("Save marks", key="save_marks", type="primary", icon=":material/save:"):
            rows = [{"roll_no": _val(r["roll_no"]), **{c: _val(r[c]) for c in cols}}
                    for _, r in edited.iterrows()]
            records, errors = mr.table_to_records(rows, questions)
            if errors:
                _show_errors(errors)
            else:
                db.save_marks(sid, component, records)
                _bump()
                flash(f"Saved marks for {len({r[1] for r in records})} students.")
                st.rerun()
