"""Student: Subject Dashboard (Goal, CIA Analysis, Weak Topics, Progress and ESE tabs)."""
from __future__ import annotations

from html import escape

import streamlit as st

import config
from core import analysis, db, insights, suggestions
from ui import components, plotly_theme, profile
from ui.weak_topics import render_weak_topics

num = components.num

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


def list_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def formula_card(weight: float) -> str:
    cia, ese = round(weight * 100), round((1 - weight) * 100)
    parts = " + ".join(f"{k}/{config.COMPONENTS[k]}" for k in config.CIA_COMPONENTS)
    m = config.STRETCH_MARGIN
    rules = [(analysis.ON_TRACK, "needed ≤ your average"), (analysis.STRETCH, f"up to {m} pts above"),
             (analysis.AT_RISK, f"more than {m} pts above"), (analysis.OUT_OF_REACH, "over 100%")]
    body = (components.formula(f"Final = CIA total × {weight:g} + ESE × {1 - weight:g}",
                               f"CIA total = {parts} (out of {config.CIA_TOTAL_MAX}); "
                               f"CIA {cia} + ESE {ese} = 100")
            + components.formula(f"ESE below {config.ESE_PASS_MARK} is a fail, whatever the CIA "
                                 "total.", fail=True)
            + '<div class="gl-eyebrow">Status rule · % needed vs your average so far</div>'
            + "".join(components.rule_row(components.status_pill(s), t) for s, t in rules)
            + components.rule_row("", "Achieved or Missed once nothing is left to sit. "
                                      "A failed ESE is always Missed."))
    return components.section_card("How your final mark works", body)


def final_verdict(goal: analysis.GoalResult, target: float, ese: float | None) -> str:
    if goal.status == analysis.ACHIEVED:
        return "You reached it."
    if ese is not None and not analysis.passed_ese(ese):
        return f"Your ESE of {num(ese)} is below the pass mark of {config.ESE_PASS_MARK}, so the goal is missed."
    return f"You finished {num(target - goal.final)} short."


def render_goal() -> None:
    components.render(components.tab_heading(
        "Your goal", f"Where your final mark in {subject['code']} stands against your target."))
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
    goal = analysis.goal_status(target, scores, weight)
    weights = {c: w for c, w in analysis.component_weights(weight).items() if w > 0}
    pending = [c for c in weights if scores.get(c) is None]
    done = [c for c in weights if scores.get(c) is not None]
    eyebrow = f'Your goal plan · {subject["code"]}'

    # --- hero -----------------------------------------------------------------
    if goal.status == analysis.NO_DATA:
        hero = components.hero_banner(
            f"Target {num(target)}/100: set — no data yet",
            "No marks have been entered for you in this subject yet. "
            "Your goal status appears as soon as the first paper is in.", eyebrow)
    elif not pending:
        hero = components.hero_banner(
            f"Final mark {num(goal.final)}/100: {goal.status}",
            f"Your target was {num(target)}. {final_verdict(goal, target, scores.get('ESE'))}", eyebrow)
    else:
        cards = "".join(components.target_card(
            f"{c} target", f"{max(0.0, goal.required_pct) / 100 * config.COMPONENTS[c]:.0f}",
            f"/ {config.COMPONENTS[c]}") for c in pending)
        if goal.required_pct <= 0:
            title, text = "Your target is already covered", "You have earned enough marks to reach it."
        else:
            title = f"You need an average of {goal.required_pct:.0f}% in {list_names(pending)}"
            text = (f"That keeps your {num(target)}/100 target in reach. "
                    f"ESE below {config.ESE_PASS_MARK} is still a fail.")
        hero = components.hero_banner(title, text, eyebrow, cards)
    components.render(hero)
    st.write("")

    # --- KPIs -----------------------------------------------------------------
    label = None
    if goal.status == analysis.NO_DATA:
        sub, label = "Waiting for your first marks", "Set — no data yet"
    elif not pending:
        sub = f"Final mark {num(goal.final)}"
    else:
        sub = f"Needs {max(0.0, goal.required_pct):.0f}% · your average so far {goal.current_pct:.0f}%"
    kpis = [components.kpi_card("Target", f"{num(target)} /100", "Set on My Subjects"),
            components.kpi_card("Earned so far", f"{num(goal.earned)} marks",
                                (" + ".join(done) + ", weighted") if done else "Nothing scored yet"),
            components.kpi_card("Still available", f"{num(goal.remaining_weight)} marks",
                                (" + ".join(pending) + ", weighted") if pending
                                else "Nothing left to sit"),
            components.status_kpi_card("Status", goal.status, sub, label)]
    for col, kpi in zip(st.columns(4), kpis):
        col.markdown(kpi, unsafe_allow_html=True)
    st.write("")

    # --- chart + formula --------------------------------------------------------
    left, right = st.columns([2, 1])
    with left, components.card("goal_chart"):
        components.render(components.card_title(
            "Score by component", "% of each paper's maximum. Dashed bars are still to write; "
                                  "the dashed line is the required %."))
        scored = {c: scores[c] / config.COMPONENTS[c] * 100 for c in done}
        st.plotly_chart(plotly_theme.goal_figure(
            scored, pending, goal.required_pct if pending else None, order=list(weights)),
            key="goal_chart_fig")
    with right:
        components.render(formula_card(weight))

    # --- components table -------------------------------------------------------
    rows = []
    for c, w in weights.items():
        mx, sc = config.COMPONENTS[c], scores.get(c)
        rows.append([escape(c), num(mx), "Not yet" if sc is None else num(sc),
                     "–" if sc is None else f"{sc / mx * 100:.1f}%", num(w)])
    with components.card("goal_table"):
        components.render(components.card_title("Components"))
        components.render(components.table(
            ["Component", "Max marks", "Your marks", "Your %", "Share of final mark"], rows,
            numeric=(1, 2, 3, 4), classes={0: "gl-q"}))


# --- CIA Analysis (SAN-124) ----------------------------------------------------
def _toggle_flag(key: str, student_id: int, question_id: int, label: str) -> None:
    if st.session_state[key]:
        db.set_silly_flag(student_id, question_id)
        st.toast(f"{label} flagged as a silly slip. Your analysis is updated.")
    else:
        db.clear_silly_flag(student_id, question_id)
        st.toast(f"Silly-slip flag removed from {label}.")


def time_pressure_text(a: analysis.PaperAnalysis) -> tuple[str, str]:
    s = analysis.time_pressure_summary(a)
    k = len(s.last_q_nos)
    names = [f"Q{q}" for q in s.last_q_nos]
    first = s.first_q_nos
    rest = f"Q{first[0]}" if len(first) == 1 else f"Q{first[0]}–Q{first[-1]}"
    title = "Time pressure on the last " + ("question" if k == 1 else f"{k} questions")
    text = (f"{list_names(names)} earned {num(s.last_score)} of {num(s.last_max)} marks "
            f"({s.last_pct:.0f}%) while you averaged {s.first_pct:.0f}% on {rest}. You dropped "
            f"{s.student_drop:.0f} points; the class dropped {s.class_drop:.0f}. In the next CIA, "
            "keep 10 minutes for the final questions or answer the short ones first.")
    return title, text


def render_cia(analyses: dict[str, analysis.PaperAnalysis]) -> None:
    waiting = [c for c in config.CIA_COMPONENTS if c not in analyses]
    components.render(components.tab_heading(
        "CIA paper analysis", "Question by question, against the class. The topper is never named."
        + (f" {list_names(waiting)}: not yet." if analyses and waiting else "")))
    if not analyses:
        components.render(components.coming_soon(
            "No CIA marks yet", "Your question-by-question analysis appears once your faculty "
            "enters marks for a CIA paper.", "&#128203;"))
        return
    papers = list(analyses)
    key = f"cia_paper_{subject['id']}"
    if st.session_state.get(key) not in papers:
        st.session_state[key] = papers[0]

    with components.card("cia_analysis"):
        head, picker = st.columns([3, 2], vertical_alignment="center")
        with picker:
            comp = st.segmented_control("Paper", papers, key=key, required=True,
                                        label_visibility="collapsed", width="stretch")
        a = analyses[comp]
        t = a.table
        with head:
            components.render(components.card_title(
                f"{comp} · {len(t)} question{'s' if len(t) != 1 else ''}"))

        unit = f"/ {num(a.max_total)}"
        tiles = [("Your total", num(a.total), unit, "&#9998;", "honey"),
                 ("Class topper", num(a.topper_total), unit, "&#9733;", "sunflower"),
                 ("Class average", num(a.class_avg_total), unit, "&#8960;", "lemon"),
                 ("Percentile", components.ordinal(a.percentile), f"of {a.class_size}", "%",
                  "bronze")]
        for col, tile in zip(st.columns(4), tiles):
            col.markdown(components.stat_tile(*tile), unsafe_allow_html=True)

        if a.time_pressure:
            components.render(components.warning_banner(*time_pressure_text(a)))

        rows = [{"q_no": r.q_no, "topic": r.topic or "Untagged", "max": num(r.max_marks),
                 "you": "–" if r.blank else num(r.score), "topper": num(r.topper),
                 "class_avg": num(r.class_avg), "percentile": components.ordinal(r.percentile),
                 "mistake": r.mistake_type} for r in t.itertuples()]
        components.render(components.question_table(rows))

        left, right = st.columns([3, 2])
        labels = [f"Q{int(q)}" for q in t["q_no"]]
        with left, components.card("cia_compare"):
            components.render(components.chart_title("You vs topper vs class", "% of question max"))
            st.plotly_chart(plotly_theme.question_compare_figure(
                labels, list(t["score"].fillna(0) / t["max_marks"] * 100),
                list(t["topper"] / t["max_marks"] * 100),
                list(t["class_avg"] / t["max_marks"] * 100)), key=f"cia_compare_{comp}")
        with right, components.card("cia_donut"):
            components.render(components.chart_title(
                f"Where the {num(a.max_total - a.total)} marks went"))
            if a.max_total - a.total <= 0:
                st.caption("Full marks: nothing lost on this paper.")
            else:
                st.plotly_chart(plotly_theme.mistake_donut_figure(
                    analysis.marks_lost_by_mistake(t)), key=f"cia_donut_{comp}")

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
    data_version = st.session_state.get("data_version", 0)
    for start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, (gain, r, tip) in zip(cols, cards[start:start + 3]):
            qid = int(r["question_id"])
            with col, components.tip_card(f"{qid}", r["mistake_type"]):
                components.render(components.tip_card_html(
                    r["mistake_type"], gain, suggestions.tip_title(r), tip))
                if not r["blank"] and r["score"] < r["max_marks"]:
                    fkey = f"flag_{student['id']}_{qid}_{data_version}"
                    st.checkbox("Right method, but I made a calculation/silly slip",
                                value=bool(r["flagged"]), key=fkey, on_change=_toggle_flag,
                                args=(fkey, student["id"], qid, f"Q{int(r['q_no'])}"))


# --- Progress (SAN-124) -----------------------------------------------------------
def render_progress(analyses: dict[str, analysis.PaperAnalysis]) -> None:
    components.render(components.tab_heading(
        "Are your weak topics improving?", "% scored on each topic's questions, paper by paper."))
    rows = analysis.topic_progress(analyses)
    if rows.empty:
        components.render(components.coming_soon(
            "No progress to show yet", "Topic percentages appear once your CIA marks are in.",
            "&#128200;"))
        return
    papers = list(dict.fromkeys(rows["component"]))
    trends = analysis.topic_trends(rows)

    with components.card("progress"):
        if len(papers) < 2:
            components.render(components.callout(
                f"Progress appears after two papers. Only {papers[0]} has marks so far; "
                "your topic lines start once the next CIA is in."))
        elif trends.empty:
            components.render(components.callout(
                "No topic has been asked in two papers yet, so there is no trend to draw."))
        else:
            components.render(components.card_title(
                "Topic trend", "First paper to latest paper; biggest gain first."))
            components.render(components.progress_chips(trends))
            st.plotly_chart(plotly_theme.topic_progress_figure(
                analysis.trend_lines(rows), list(config.CIA_COMPONENTS)), key="progress_fig")
        with st.expander("Every topic by paper"):
            table = (rows.pivot_table(index="topic", columns="component", values="pct", sort=False)
                     .reindex(columns=papers).round(0))
            st.dataframe(table.rename_axis("Topic").rename(columns=lambda c: f"{c} %"))


# --- ESE (SAN-127) ------------------------------------------------------------------
def render_ese(analyses: dict[str, analysis.PaperAnalysis]) -> None:
    components.render(components.tab_heading(
        "ESE result", "Your end-semester exam, your final mark and your presentation feedback."))
    scores = insights.student_component_scores(subject["id"], student["roll_no"])
    ese = scores["ESE"]
    if ese is None:
        st.info("Your ESE mark has not been entered yet. Your result and feedback appear here "
                "once your faculty uploads the ESE marks.")
        return
    passed = analysis.passed_ese(ese)
    target = subject["target"]
    goal = analysis.goal_status(target or 0, scores, subject["cia_weight"])
    gap = abs(ese - config.ESE_PASS_MARK)
    with st.container(key="ese_pair"):
        left, right = st.columns(2, gap="medium")
        with left, components.card("ese_score"):
            components.render(components.card_eyebrow("ESE score"))
            components.render(components.big_figure(f"{num(ese)} / {config.COMPONENTS['ESE']}"))
            components.render(components.pill("Pass" if passed else "Fail",
                                              "ok" if passed else "at-risk"))
            st.caption(f"{num(gap)} above the pass line of {config.ESE_PASS_MARK}." if passed
                       else f"{num(gap)} below the pass line of {config.ESE_PASS_MARK}. "
                            "Plan for the supplementary exam.")
        with right, components.card("ese_final"):
            components.render(components.card_eyebrow("Final mark vs target"))
            if goal.final is None:
                components.render(components.big_figure("Pending"))
                st.caption("It is calculated once every paper has marks.")
            else:
                components.render(components.big_figure(
                    f"{num(goal.final)} / 100",
                    f"target {num(target)}" if target is not None else ""))
                if target is not None:
                    components.render(components.status_pill(goal.status))
                if not passed:
                    st.caption(f"ESE below {config.ESE_PASS_MARK} is a fail, whatever your CIA total.")
    st.write("")

    review = db.get_review(subject["id"], student["roll_no"])
    if review and review["published"] and (review["final_review"] or "").strip():
        good, improve = suggestions.split_review(review["final_review"])
        components.render(components.section_head("Presentation feedback", "From your faculty"))
        shown = [c for c in (("Doing well", good), ("Improve", improve)) if c[1]]
        with st.container(key="ese_feedback_pair"):
            for col, (title, body) in zip(st.columns(len(shown), gap="medium"), shown):
                with col, components.card("ese_" + title.lower().replace(" ", "_")):
                    components.render(components.card_title(title))
                    st.markdown(body)
    else:
        components.render(components.callout("Your faculty hasn't published a review yet."))

    if not passed:
        st.write("")
        components.render(components.section_head(
            "Focus for supplementary exam", "The topics that cost you the most marks across your CIAs"))
        render_weak_topics(subject, insights.weak_topic_rows(subject["id"], analyses), key="ese_focus")


analyses = insights.student_paper_analyses(subject["id"], student["roll_no"], student["id"])
with tab_goal:
    render_goal()
with tab_cia:
    render_cia(analyses)
with tab_weak:
    components.render(components.tab_heading(
        "Weak topics & resources",
        f"{subject['code']} {subject['name']} · ranked by marks lost across your CIAs."))
    render_weak_topics(subject, insights.weak_topic_rows(subject['id'], analyses))
with tab_progress:
    render_progress(analyses)
with tab_ese:
    render_ese(analyses)
