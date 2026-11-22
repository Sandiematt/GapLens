"""Student: Subject Dashboard (Goal, CIA Analysis and Progress built; others are placeholders)."""
from __future__ import annotations

import math
from html import escape

import pandas as pd
import streamlit as st

import config
from core import analysis, db, insights, suggestions
from ui import components, plotly_theme, profile
from ui.weak_topics import render_weak_topics

student = profile.current_student()
subject = profile.current_subject(student)

if student is None:
    components.render(components.page_header("Subject Dashboard"))
    st.info("No student profile exists yet. Create one from the sidebar.")
    st.stop()
if subject is None:
    components.render(components.page_header(
        f'Welcome back, {student["name"]}', "You are not enrolled in any subject yet."))
    st.info("Enroll in a subject from My Subjects to see its dashboard.")
    st.page_link("views/student_subjects.py", label="Go to My Subjects", icon=":material/grid_view:")
    st.stop()

components.render(components.page_header(
    f'Welcome back, {student["name"]}',
    f"Here's where you stand in {subject['code']} {subject['name']}.",
    components.pill(student["class_name"], "gold")))

tab_goal, tab_cia, tab_weak, tab_progress, tab_ese = st.tabs(
    ["Goal", "CIA Analysis", "Weak Topics & Resources", "Progress", "ESE"])

for tab, name, ticket in [(tab_ese, "ESE", "SAN-127")]:
    with tab:
        components.render(components.coming_soon(f"{name}: coming in {ticket}",
                                                 "This tab arrives in a later ticket."))


def fmt(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def list_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def status_rules_html() -> str:
    m = config.STRETCH_MARGIN
    rules = [("On track", "needed ≤ your average"), ("Stretch", f"up to {m} pts above"),
             ("At risk", f"more than {m} pts above"), ("Out of reach", "over 100%")]
    return "".join(f'<div class="gl-rule">{components.status_pill(s)}<span>{t}</span></div>'
                   for s, t in rules)


def formula_card(weight: float) -> str:
    cia, ese = round(weight * 100), round((1 - weight) * 100)
    parts = " + ".join(f"{k}/{config.COMPONENTS[k]}" for k in config.CIA_COMPONENTS)
    body = (f'<div class="gl-formula">Final = CIA total × {weight:g} + ESE × {1 - weight:g}'
            f'<br><span style="font-weight:400;font-size:12px">CIA total = {parts} '
            f'(out of {config.CIA_TOTAL_MAX}); CIA {cia} + ESE {ese} = 100</span></div>'
            f'<div class="gl-formula" style="background:#FEE2E2;border-color:#FEE2E2;color:#B91C1C">'
            f'ESE below {config.ESE_PASS_MARK} is a fail, whatever the CIA total.</div>'
            f'<div class="gl-eyebrow">Status rule · % needed vs your average so far</div>'
            f'{status_rules_html()}'
            f'<div class="gl-rule"><span>Achieved or Missed once nothing is left to sit.</span></div>')
    return components.section_card("How your final mark works", body)


def render_goal() -> None:
    target = subject["target"]
    if target is None:
        components.render(components.coming_soon(
            "No target set for this subject",
            "Set the mark you are aiming for in My Subjects and your goal status appears here.",
            "&#127919;"))
        st.page_link("views/student_subjects.py", label="Set a target in My Subjects",
                     icon=":material/grid_view:")
        return

    weight = subject["cia_weight"]
    scores = insights.student_component_scores(subject["id"], student["roll_no"])
    g = analysis.goal_status(target, scores, weight)
    weights = {c: w for c, w in analysis.component_weights(weight).items() if w > 0}
    pending = [c for c in weights if scores.get(c) is None]
    done = [c for c in weights if scores.get(c) is not None]
    eyebrow = f'Your goal plan · {subject["code"]}'

    # --- hero -----------------------------------------------------------------
    if g.status == "No data":
        hero = components.hero_banner(
            f"Target {fmt(target)}/100: set — no data yet",
            "No marks have been entered for you in this subject yet. "
            "Your goal status appears as soon as the first paper is in.", eyebrow)
    elif not pending:
        verdict = ("You reached it." if g.status == "Achieved"
                   else f"You finished {fmt(target - g.final)} short.")
        hero = components.hero_banner(f"Final mark {fmt(g.final)}/100: {g.status}",
                                      f"Your target was {fmt(target)}. {verdict}", eyebrow)
    else:
        cards = ""
        for c in pending:
            mx = config.COMPONENTS[c]
            cards += (f'<div class="gl-target-card"><small>{escape(c)} target</small>'
                      f'<b>{max(0.0, g.required_pct) / 100 * mx:.0f}</b> <span>/ {mx}</span></div>')
        if g.required_pct <= 0:
            title, text = "Your target is already covered", "You have earned enough marks to reach it."
        else:
            title = f"You need an average of {g.required_pct:.0f}% in {list_names(pending)}"
            text = (f"That keeps your {fmt(target)}/100 target in reach. "
                    f"ESE below {config.ESE_PASS_MARK} is still a fail.")
        hero = components.hero_banner(title, text, eyebrow, cards)
    components.render(hero)
    st.write("")

    # --- KPIs -----------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(components.kpi_card("Target", f"{fmt(target)} /100", "Set on My Subjects"),
                unsafe_allow_html=True)
    c2.markdown(components.kpi_card("Earned so far", f"{fmt(g.earned)} marks",
                                    (" + ".join(done) + ", weighted") if done else "Nothing scored yet"),
                unsafe_allow_html=True)
    c3.markdown(components.kpi_card("Still available", f"{fmt(g.remaining_weight)} marks",
                                    (" + ".join(pending) + ", weighted") if pending
                                    else "Nothing left to sit"), unsafe_allow_html=True)
    label = None
    if g.status == "No data":
        sub, label = "Waiting for your first marks", "Set — no data yet"
    elif not pending:
        sub = f"Final mark {fmt(g.final)}"
    else:
        sub = f"Needs {max(0.0, g.required_pct):.0f}% · your average so far {g.current_pct:.0f}%"
    c4.markdown(components.status_kpi_card("Status", g.status, sub, label), unsafe_allow_html=True)
    st.write("")

    # --- chart + formula --------------------------------------------------------
    left, right = st.columns([2, 1])
    with left:
        with components.card("goal_chart"):
            st.markdown("### Score by component")
            st.caption("% of each paper's maximum. Dashed bars are still to write; "
                       "the dashed line is the required %.")
            scored = {c: scores[c] / config.COMPONENTS[c] * 100 for c in done}
            st.plotly_chart(plotly_theme.goal_figure(
                scored, pending, g.required_pct if pending else None, order=list(weights)), key="goal_chart_fig")
    with right:
        components.render(formula_card(weight))

    # --- components table -------------------------------------------------------
    rows = []
    for c, w in weights.items():
        mx, sc = config.COMPONENTS[c], scores.get(c)
        rows.append({"Component": c, "Max marks": mx,
                     "Your marks": "Not yet" if sc is None else fmt(sc),
                     "Your %": "-" if sc is None else f"{sc / mx * 100:.1f}%",
                     "Share of final mark": fmt(w)})
    with components.card("goal_table"):
        st.markdown("### Components")
        st.dataframe(pd.DataFrame(rows), hide_index=True)


# --- CIA Analysis (SAN-124) ----------------------------------------------------
def _toggle_flag(key: str, student_id: int, question_id: int, label: str) -> None:
    if st.session_state[key]:
        db.set_silly_flag(student_id, question_id)
        st.toast(f"{label} flagged as a silly slip. Your analysis is updated.")
    else:
        db.clear_silly_flag(student_id, question_id)
        st.toast(f"Silly-slip flag removed from {label}.")


def time_pressure_text(a: analysis.PaperAnalysis) -> tuple[str, str]:
    t = a.table
    k = math.ceil(len(t) / 3)
    last = t.tail(k)
    names = [f"Q{int(q)}" for q in last["q_no"]]
    got, mx = last["score"].fillna(0).sum(), last["max_marks"].sum()
    last_pct = got / mx * 100
    first_q = t.head(len(t) - k)["q_no"]
    rest = (f"Q{int(first_q.iloc[0])}" if len(first_q) == 1
            else f"Q{int(first_q.iloc[0])}–Q{int(first_q.iloc[-1])}")
    title = "Time pressure on the last " + ("question" if k == 1 else f"{k} questions")
    text = (f"{list_names(names)} earned {fmt(got)} of {fmt(mx)} marks ({last_pct:.0f}%) while you "
            f"averaged {last_pct + a.student_drop:.0f}% on {rest}. You dropped "
            f"{a.student_drop:.0f} points; the class dropped {a.class_drop:.0f}. In the next CIA, "
            "keep 10 minutes for the final questions or answer the short ones first.")
    return title, text


def render_cia(analyses: dict[str, analysis.PaperAnalysis]) -> None:
    if not analyses:
        components.render(components.coming_soon(
            "No CIA marks yet", "Your question-by-question analysis appears once your faculty "
            "enters marks for a CIA paper.", "&#128203;"))
        return
    papers = list(analyses)
    key = f"cia_paper_{subject['id']}"
    if st.session_state.get(key) not in papers:
        st.session_state[key] = papers[0]
    waiting = [c for c in config.CIA_COMPONENTS if c not in analyses]

    with components.card("cia_analysis"):
        head, picker = st.columns([3, 2], vertical_alignment="center")
        with head:
            st.markdown("### CIA paper analysis")
            st.caption("Question by question, against the class. The topper is never named."
                       + (f" {list_names(waiting)}: not yet." if waiting else ""))
        with picker:
            comp = st.segmented_control("Paper", papers, key=key, required=True,
                                        label_visibility="collapsed", width="stretch")
        a = analyses[comp]
        t = a.table

        unit = f"/ {fmt(a.max_total)}"
        tiles = [("Your total", fmt(a.total), unit, "&#9998;", "honey"),
                 ("Class topper", fmt(a.topper_total), unit, "&#9733;", "sunflower"),
                 ("Class average", fmt(a.class_avg_total), unit, "&#8960;", "lemon"),
                 ("Percentile", components.ordinal(a.percentile), f"of {a.class_size}", "%",
                  "bronze")]
        for col, tile in zip(st.columns(4), tiles):
            col.markdown(components.stat_tile(*tile), unsafe_allow_html=True)

        if a.time_pressure:
            components.render(components.warning_banner(*time_pressure_text(a)))

        rows = [{"q_no": r.q_no, "topic": r.topic or "Untagged", "max": fmt(r.max_marks),
                 "you": "–" if r.blank else fmt(r.score), "topper": fmt(r.topper),
                 "class_avg": fmt(r.class_avg), "percentile": components.ordinal(r.percentile),
                 "mistake": r.mistake_type} for r in t.itertuples()]
        components.render(components.question_table(rows))

        left, right = st.columns([3, 2])
        labels = [f"Q{int(q)}" for q in t["q_no"]]
        with left:
            with components.card("cia_compare"):
                st.markdown("**You vs topper vs class** · % of question max")
                st.plotly_chart(plotly_theme.question_compare_figure(
                    labels, list(t["score"].fillna(0) / t["max_marks"] * 100),
                    list(t["topper"] / t["max_marks"] * 100),
                    list(t["class_avg"] / t["max_marks"] * 100)), key=f"cia_compare_{comp}")
        with right:
            with components.card("cia_donut"):
                lost_by = (t["max_marks"] - t["score"].fillna(0)).groupby(t["mistake_type"]).sum()
                lost = {m: float(lost_by.get(m, 0)) for m in analysis.MISTAKE_TYPES}
                st.markdown(f"**Where the {fmt(a.max_total - a.total)} marks went**")
                if a.max_total - a.total <= 0:
                    st.caption("Full marks: nothing lost on this paper.")
                else:
                    st.plotly_chart(plotly_theme.mistake_donut_figure(lost), key=f"cia_donut_{comp}")

    # --- next moves -------------------------------------------------------------
    cards = []
    for r in t.to_dict("records"):
        tip = suggestions.question_tip(r)
        if tip:
            cards.append((suggestions.potential_gain(r), r, tip))
    cards.sort(key=lambda c: (-c[0], c[1]["q_no"]))
    if not cards:
        components.render(components.callout("Full marks on every question. Nothing to fix here."))
        return
    plural = "s" if len(cards) != 1 else ""
    components.render(components.section_head(
        f"Your next moves after {comp}", f"{len(cards)} suggestion{plural} · biggest gain first"))
    dv = st.session_state.get("data_version", 0)
    for start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, (gain, r, tip) in zip(cols, cards[start:start + 3]):
            qid = int(r["question_id"])
            with col, components.tip_card(f"{qid}", r["mistake_type"]):
                components.render(components.tip_card_html(
                    r["mistake_type"], gain, suggestions.tip_title(r), tip))
                if not r["blank"] and r["score"] < r["max_marks"]:
                    fkey = f"flag_{student['id']}_{qid}_{dv}"
                    st.checkbox("Right method, but I made a calculation/silly slip",
                                value=bool(r["flagged"]), key=fkey, on_change=_toggle_flag,
                                args=(fkey, student["id"], qid, f"Q{int(r['q_no'])}"))


# --- Progress (SAN-124) -----------------------------------------------------------
def render_progress(analyses: dict[str, analysis.PaperAnalysis]) -> None:
    rows = analysis.topic_progress(analyses)
    if rows.empty:
        components.render(components.coming_soon(
            "No progress to show yet", "Topic percentages appear once your CIA marks are in.",
            "&#128200;"))
        return
    papers = list(dict.fromkeys(rows["component"]))
    counts = rows.groupby("topic_id")["component"].nunique()
    multi = rows[rows["topic_id"].isin(counts[counts >= 2].index)]

    with components.card("progress"):
        st.markdown("### Are your weak topics improving?")
        st.caption("% scored on each topic's questions, paper by paper.")
        if len(papers) < 2:
            components.render(components.callout(
                f"Progress appears after two papers. Only {papers[0]} has marks so far; "
                "your topic lines start once the next CIA is in."))
        elif multi.empty:
            components.render(components.callout(
                "No topic has been asked in two papers yet, so there is no trend to draw."))
        else:
            chips = []
            for _tid, g in multi.groupby("topic_id", sort=False):
                first, last = g["pct"].iloc[0], g["pct"].iloc[-1]
                chips.append((last - first, g["topic"].iloc[0], first, last))
            chips.sort(key=lambda c: -c[0])
            components.render('<div class="gl-chips">' + "".join(
                components.progress_chip(topic, first, last) for _d, topic, first, last in chips)
                + "</div>")
            rank = {topic: i for i, (_d, topic, _f, _l) in enumerate(chips)}  # biggest gain first
            multi = multi.iloc[multi["topic"].map(rank).argsort(kind="stable")]
            st.plotly_chart(plotly_theme.topic_progress_figure(multi, list(config.CIA_COMPONENTS)),
                            key="progress_fig")
        with st.expander("Every topic by paper"):
            table = (rows.pivot_table(index="topic", columns="component", values="pct", sort=False)
                     .reindex(columns=papers).round(0))
            st.dataframe(table.rename_axis("Topic").rename(columns=lambda c: f"{c} %"))


analyses = insights.student_paper_analyses(subject["id"], student["roll_no"], student["id"])
with tab_goal:
    render_goal()
with tab_cia:
    render_cia(analyses)
with tab_weak:
    components.render(components.page_header(
        'Weak topics & resources',
        f"{subject['code']} {subject['name']} · ranked by marks lost across your CIAs."))
    render_weak_topics(subject, insights.weak_topic_rows(subject['id'], analyses))
with tab_progress:
    render_progress(analyses)
