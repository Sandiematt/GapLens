"""Faculty: Class Insights (heatmap, topics to revise, early warning, silly-error flags).

Everything is read from the database on every run (no caching), so a new marks
upload or student flag shows up on the next load.
"""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

import config
from core import analysis, db, insights
from ui import components, plotly_theme, profile

faculty = profile.current_faculty()
components.render(components.page_header(
    "Class Insights", "Where the class lost marks, and who needs a nudge."))
if faculty is None:
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()
subjects = db.list_subjects(faculty_id=faculty["id"])
if not subjects:
    st.info("Create a subject first, then enter CIA marks to see insights.")
    st.stop()

data_version = st.session_state.get("data_version", 0)
labels = {s["id"]: f'{s["code"]} {s["name"]}' for s in subjects}
c1, c2 = st.columns(2)
by_label = {v: k for k, v in labels.items()}
sid = by_label[c1.selectbox("Subject", list(by_label), key=f"ins_subject_{data_version}")]

papers = {comp: insights.paper_frames(sid, comp) for comp in config.CIA_COMPONENTS}
papers = {c: f for c, f in papers.items() if not f[1].empty}  # only papers with marks
ALL = "All CIAs"
options = list(papers) + ([ALL] if papers else [])
if not options:
    st.info("No CIA marks have been entered for this subject yet. Add them in Papers & Marks.")
    st.stop()
choice = c2.selectbox("Paper", options, key=f"ins_paper_{data_version}_{sid}")
single = choice != ALL
chosen = [papers[choice]] if single else list(papers.values())

if single:
    with components.card("ins_heat"):
        questions, marks = papers[choice]
        matrix = analysis.class_question_matrix(questions, marks)
        components.render(components.section_head(
            f"Class heatmap · {choice}", f"{len(matrix)} students · % of each question's marks"))
        st.plotly_chart(plotly_theme.class_heatmap_figure(matrix), key=f"ins_heat_{data_version}_{sid}_{choice}")

with components.card("ins_topics"):
    topics = analysis.class_topic_pct(chosen)
    components.render(components.section_head(
        "Revise these in class", f"Class average per topic · {choice}, worst first"))
    if topics.empty:
        st.caption("No tagged questions to summarise.")
    else:
        st.plotly_chart(plotly_theme.revise_topics_figure(topics["topic"], topics["pct"]),
                        key=f"ins_topics_{data_version}_{sid}_{choice}")

overview = insights.class_overview(sid)
flagged = [r for r in overview if r["reasons"]]
with components.card("ins_warn"):
    components.render(components.section_head(
        "Early warning", f"{len(flagged)} of {len(overview)} students flagged"))
    if not flagged:
        st.caption("Nobody is flagged right now.")
    else:
        flagged.sort(key=lambda r: (r["cia_pct"] is None, r["cia_pct"] or 0))
        body = [[escape(r["roll"]), escape(r["name"]),
                 components.num(r["target"]) if r["target"] is not None else "&ndash;",
                 components.num(r["cia_pct"]) + "%" if r["cia_pct"] is not None else "&ndash;",
                 components.status_pill(r["status"]), escape("; ".join(r["reasons"]))]
                for r in flagged]
        components.render(components.table(
            ["Roll", "Name", "Target", "CIA %", "Status", "Reason"], body, numeric=(2, 3)))

if single:
    with components.card("ins_flags"):
        counts = pd.DataFrame(db.count_silly_flags(sid, choice))
        components.render(components.section_head(
            "Silly-error flags", "Students who flagged each question as right method, wrong answer"))
        if counts.empty:
            st.caption("This paper has no questions.")
        else:
            st.plotly_chart(plotly_theme.silly_flags_figure(
                [f"Q{n}" for n in counts["q_no"]], counts["flags"]),
                key=f"ins_flags_{data_version}_{sid}_{choice}")
            if counts["flags"].sum() == 0:
                st.caption("No flags yet.")

components.render(components.callout(
    "Real-time: this page re-reads the database on every load, so new marks and "
    "student flags appear as soon as you reload."))
