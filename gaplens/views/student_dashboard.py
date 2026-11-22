"""Student: Subject Dashboard (Goal tab built; other tabs are placeholders)."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

import config
from core import analysis, insights
from ui import components, plotly_theme, profile

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

for tab, name, ticket in [(tab_cia, "CIA Analysis", "SAN-124"),
                          (tab_weak, "Weak Topics & Resources", "SAN-125"),
                          (tab_progress, "Progress", "SAN-124"), (tab_ese, "ESE", "SAN-127")]:
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


with tab_goal:
    target = subject["target"]
    if target is None:
        components.render(components.coming_soon(
            "No target set for this subject",
            "Set the mark you are aiming for in My Subjects and your goal status appears here.",
            "&#127919;"))
        st.page_link("views/student_subjects.py", label="Set a target in My Subjects",
                     icon=":material/grid_view:")
        st.stop()

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
