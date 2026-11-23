"""Student Home: overview dashboard (KPIs, trends, scores) + My Subjects enrollment."""
from __future__ import annotations

from html import escape

import streamlit as st

import config
from core import analysis, db, insights
from ui import components, plotly_theme, profile
from ui.flash import flash

student = profile.current_student()
if student is None:
    components.render(components.page_header("My subjects"))
    st.info("No student profile exists yet. Create one from the sidebar.")
    st.stop()

subjects = db.list_subjects(class_name=student["class_name"])
topics_by_subject = db.list_topics_by_subject(s["id"] for s in subjects)
enrollments = {e["subject_id"]: e for e in db.list_enrollments(student["id"])}
enrolled_subjects = [s for s in subjects if s["id"] in enrollments]
enrolled_count = len(enrolled_subjects)


def _short_label(text: str, limit: int = 10) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _collect_home_metrics() -> dict:
    """Gather real live scores, goals, topic percentages, pending papers and notifications."""
    comp_labels: list[str] = []
    comp_pcts: list[float] = []
    comp_details: list[str] = []

    topic_labels: list[str] = []
    topic_pcts: list[float] = []
    topic_details: list[str] = []

    all_pcts: list[float] = []
    targets: list[float] = []
    goal_statuses: list[tuple[str, str, analysis.GoalResult]] = []
    pending_items: list[str] = []
    weak_count = 0
    notifications: list[dict] = []

    for subj in enrolled_subjects:
        sid = subj["id"]
        code = subj["code"]
        target = enrollments[sid]["target"]
        if target is not None:
            targets.append(float(target))

        scores = insights.student_component_scores(sid, student["roll_no"])
        weights = {c: w for c, w in analysis.component_weights(subj["cia_weight"]).items() if w > 0}
        subj_pending: list[str] = []
        for comp in weights:
            sc = scores.get(comp)
            mx = config.COMPONENTS[comp]
            if sc is None:
                pending_items.append(f"{code} {comp}")
                subj_pending.append(comp)
            else:
                pct = sc / mx * 100.0
                all_pcts.append(pct)
                short_comp = comp.replace("CIA-", "C")
                comp_labels.append(f"{code[-3:]} {short_comp}")
                comp_pcts.append(round(pct, 1))
                comp_details.append(
                    f"{code} {subj['name']} · {comp}: {components.num(sc)}/{mx} ({pct:.1f}%)")

        if subj_pending:
            notifications.append({
                "title": f"{code} · Upcoming assessments",
                "body": f"{subj['name']}: {', '.join(subj_pending)} not graded yet.",
                "kind": "info",
                "subject_id": sid,
            })

        if target is not None:
            g = analysis.goal_status(target, scores, subj["cia_weight"])
            goal_statuses.append((code, subj["name"], g))
            if g.status in (analysis.AT_RISK, analysis.OUT_OF_REACH, analysis.MISSED):
                notifications.append({
                    "title": f"{code} · Goal {g.status.lower()}",
                    "body": f"Target {components.num(target)}/100 in {subj['name']} needs attention.",
                    "kind": "alert",
                    "subject_id": sid,
                })
            elif g.status == analysis.STRETCH and g.required_pct is not None:
                notifications.append({
                    "title": f"{code} · Stretch target",
                    "body": f"Need {g.required_pct:.0f}% average in remaining papers to hit {components.num(target)}.",
                    "kind": "alert",
                    "subject_id": sid,
                })

        review = db.get_review(sid, student["roll_no"])
        if review and review["published"] and (review["final_review"] or "").strip():
            notifications.append({
                "title": f"{code} · ESE feedback published",
                "body": f"Your faculty published presentation feedback for {subj['name']}.",
                "kind": "ok",
                "subject_id": sid,
            })

        analyses = insights.student_paper_analyses(sid, student["roll_no"], student["id"])
        if analyses:
            losses = analysis.topic_losses([a.table for a in analyses.values()])
            if not losses.empty:
                big_gaps = losses[losses["lost_pct"] >= config.BIG_GAP_PCT]
                weak_count += int(len(big_gaps))
                for rec in big_gaps.head(2).to_dict("records"):
                    notifications.append({
                        "title": f"{code} · Big gap in {rec['topic']}",
                        "body": (f"Lost {components.num(rec['lost'])} of {components.num(rec['max'])} "
                                 f"marks ({rec['lost_pct']:.0f}%) — review basics in Weak Topics."),
                        "kind": "alert",
                        "subject_id": sid,
                    })
            rows = analysis.topic_progress(analyses)
            if not rows.empty:
                per_topic = rows.groupby("topic", sort=False)["pct"].mean()
                for topic, pct in per_topic.items():
                    topic_labels.append(_short_label(str(topic), 11))
                    topic_pcts.append(round(float(pct), 1))
                    topic_details.append(f"{code} · {topic}")

    unenrolled = [s for s in subjects if s["id"] not in enrollments]
    if unenrolled:
        names = ", ".join(f"{s['code']} {s['name']}" for s in unenrolled[:2])
        notifications.append({
            "title": f"{len(unenrolled)} subject{'s' if len(unenrolled) != 1 else ''} available to enroll",
            "body": f"Available in {student['class_name']}: {names}.",
            "kind": "info",
            "subject_id": None,
        })

    # Keep line chart crisp (up to 12 points across enrolled subjects)
    if len(topic_labels) > 12:
        step = max(1, len(topic_labels) // 12)
        topic_labels = topic_labels[::step][:12]
        topic_pcts = topic_pcts[::step][:12]
        topic_details = topic_details[::step][:12]

    avg_pct = sum(all_pcts) / len(all_pcts) if all_pcts else None
    avg_target = sum(targets) / len(targets) if targets else None
    return {
        "avg_pct": avg_pct,
        "avg_target": avg_target,
        "targets_set": len(targets),
        "graded_count": len(all_pcts),
        "pending_items": pending_items,
        "weak_count": weak_count,
        "goal_statuses": goal_statuses,
        "notifications": notifications,
        "comp_labels": comp_labels,
        "comp_pcts": comp_pcts,
        "comp_details": comp_details,
        "topic_labels": topic_labels,
        "topic_pcts": topic_pcts,
        "topic_details": topic_details,
    }


metrics = _collect_home_metrics()
notifications = metrics["notifications"]
read_key = f"home_notif_read_{student['id']}_{st.session_state.get('data_version', 0)}"
is_read = bool(st.session_state.get(read_key, False))
unread_count = 0 if is_read else len(notifications)


def _clear_search() -> None:
    st.session_state["home_search"] = None


def _toggle_read(value: bool) -> None:
    st.session_state[read_key] = value


search_options: list[str] = []
for _s in subjects:
    search_options.append(f'{_s["code"]} · {_s["name"]}')
    for _t in topics_by_subject[_s["id"]]:
        search_options.append(f'{_t["title"]} ({_s["code"]})')


# ===================== 1. FUNCTIONAL TOP WHITE HEADER BAR =====================
with st.container(key="home_topbar"):
    tb_brand, tb_search, tb_notif, tb_help, tb_user = st.columns(
        [2.0, 2.5, 0.85, 0.55, 1.9], gap="small", vertical_alignment="center")
    with tb_brand:
        components.render(components.home_topbar_brand())
    with tb_search:
        raw_search = st.selectbox(
            "Search",
            options=search_options,
            index=None,
            key="home_search",
            placeholder="Search subjects, topics, faculty…",
            accept_new_options=True,
            label_visibility="collapsed",
        )
        search_query = (raw_search or "").strip()
    with tb_notif:
        notif_wrap_key = "home_notif_unread" if unread_count > 0 else "home_notif_read"
        with st.container(key=notif_wrap_key):
            with st.popover(f"{unread_count}", icon=":material/notifications:", width="stretch"):
                st.markdown(f"**Notifications** · {len(notifications)} active")
                if not notifications:
                    st.caption("You're all caught up! No pending alerts right now.")
                else:
                    for idx_n, item in enumerate(notifications[:6]):
                        components.render(components.notification_item(
                            item["title"], item["body"], item["kind"]))
                        if item["subject_id"] is not None:
                            if st.button("Open dashboard", key=f"notif_go_{idx_n}_{item['subject_id']}",
                                         icon=":material/arrow_forward:", icon_position="right"):
                                profile.select_subject(item["subject_id"])
                                st.switch_page("views/student_dashboard.py")
                    if not is_read:
                        st.button("Mark all read", key="notif_mark_read",
                                  on_click=_toggle_read, args=(True,))
                    else:
                        st.button("Mark as unread", key="notif_mark_unread",
                                  on_click=_toggle_read, args=(False,))
    with tb_help:
        with st.popover("", icon=":material/help:", width="stretch"):
            st.markdown("**Quick Guide · GapLens**")
            st.markdown(
                f"- **Final mark**: `CIA total × weight + ESE × (1 − weight)`\n"
                f"- **ESE pass mark**: `{config.ESE_PASS_MARK} / 100` (below this is a fail)\n"
                f"- **Search bar**: Filter subjects, faculty, or syllabus topics live\n"
                f"- **Sidebar**: Switch active subject, update student profile, or sign out"
            )
    with tb_user:
        components.render(components.home_topbar_user(
            student["name"], f'{student["roll_no"]} · {student["class_name"]}'))


# Filter subjects & topics when search query is active
def _filter_subjects(query: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    if not query:
        return subjects, []
    q = query.lower()
    # Handle autocomplete labels like "MCA231 · Data Structures" or "Recursion (MCA231)"
    terms = [q]
    if " · " in q:
        terms.extend(part.strip() for part in q.split(" · ") if part.strip())
    if "(" in q and q.endswith(")"):
        topic_part, code_part = q.rsplit("(", 1)
        if topic_part.strip():
            terms.append(topic_part.strip())
        if code_part[:-1].strip():
            terms.append(code_part[:-1].strip())
    matched_subjects: list[dict] = []
    matched_topics: list[tuple[dict, str]] = []
    for subj in subjects:
        subj_topics = topics_by_subject[subj["id"]]
        topic_hits = [
            t["title"] for t in subj_topics
            if any(term in t["title"].lower() for term in terms)
        ]
        for title in topic_hits:
            matched_topics.append((subj, title))
        haystack = f'{subj["code"]} {subj["name"]} {subj["faculty_name"]} {subj["class_name"]}'.lower()
        if any(term in haystack for term in terms) or topic_hits:
            matched_subjects.append(subj)
    return matched_subjects, matched_topics


filtered_subjects, matched_topics = _filter_subjects(search_query)

if search_query:
    topic_chips = "".join(
        components.pill(f'{s["code"]} · {title}', "gold")
        for s, title in matched_topics[:6]
    )
    sb_left, sb_right = st.columns([5, 1], vertical_alignment="center")
    with sb_left:
        components.render(
            f'<div class="gl-search-banner"><div>'
            f'Showing <b>{len(filtered_subjects)}</b> of {len(subjects)} subjects matching '
            f'<b>&ldquo;{escape(search_query)}&rdquo;</b>'
            + (f'<div class="gl-pill-row">{topic_chips}</div>' if topic_chips else "")
            + '</div></div>')
    with sb_right:
        st.button("Clear", key="home_clear_search", on_click=_clear_search,
                  icon=":material/close:")

# ===================== 2. HOME TITLE & BREADCRUMB =====================
components.render(components.home_breadcrumb(
    "Home",
    "HOME > MY SUBJECTS",
    components.pill(f"{enrolled_count} enrolled", "ok")
    + components.pill(
        f'{len(subjects)} subject{"s" if len(subjects) != 1 else ""} in {student["class_name"]}',
        "slate"),
))

# ===================== 3. ROW 1: FOUR DARK-HEADED KPI CARDS =====================
avg_pct = metrics["avg_pct"]
avg_target = metrics["avg_target"]

if avg_pct is not None and avg_target is not None:
    diff = avg_pct - avg_target
    avg_delta = f"{'+' if diff >= 0 else ''}{diff:.1f}%"
    avg_sub = "VS AVG TARGET"
    avg_pos = diff >= 0
elif avg_pct is not None:
    avg_delta = f'{metrics["graded_count"]} PAPERS'
    avg_sub = "SCORED SO FAR"
    avg_pos = True
else:
    avg_delta = ""
    avg_sub = "NO MARKS YET"
    avg_pos = True

enroll_pct = round(enrolled_count / len(subjects) * 100) if subjects else 0
target_val = f"{avg_target:.0f}%" if avg_target is not None else "—"
target_delta = f'{metrics["targets_set"]}/{enrolled_count}' if enrolled_count else "0"
graded_delta = (f'{len(metrics["pending_items"])} LEFT'
                if metrics["pending_items"] else "ALL GRADED")

kpi_cards = [
    components.home_kpi_card(
        "OVERALL AVERAGE",
        f"{avg_pct:.1f}%" if avg_pct is not None else "—",
        avg_delta,
        avg_sub,
        components.ICON_TREND_UP,
        icon_tone="dark",
        positive=avg_pos,
    ),
    components.home_kpi_card(
        "ENROLLED SUBJECTS",
        f"{enrolled_count} / {len(subjects)}",
        f"{enroll_pct}%",
        f'OF {student["class_name"]} COURSES',
        components.ICON_BOOK,
        icon_tone="green",
        positive=enrolled_count > 0,
    ),
    components.home_kpi_card(
        "AVG TARGET MARK",
        target_val,
        target_delta,
        "TARGETS CONFIGURED",
        components.ICON_BARS,
        icon_tone="coral",
        positive=metrics["targets_set"] > 0,
    ),
    components.home_kpi_card(
        "PAPERS GRADED",
        str(metrics["graded_count"]),
        graded_delta,
        "CIA & ESE PAPERS",
        components.ICON_TARGET,
        icon_tone="dark",
        positive=len(metrics["pending_items"]) == 0,
    ),
]
for col, html in zip(st.columns(4, gap="medium"), kpi_cards):
    col.markdown(html, unsafe_allow_html=True)

st.write("")

# ===================== 4. ROW 2: MINI CARDS + PERCENTAGE LINE CHART =====================
r2_left, r2_right = st.columns([1, 2.25], gap="medium")

with r2_left:
    if metrics["goal_statuses"]:
        on_track = sum(1 for _, _, g in metrics["goal_statuses"]
                       if g.status in (analysis.ON_TRACK, analysis.ACHIEVED))
        code0, _name0, g0 = metrics["goal_statuses"][0]
        health_metric = (f"{on_track}/{len(metrics['goal_statuses'])} ON TRACK"
                         if on_track else f"{code0}: {g0.status.upper()}")
        health_sub = (f'{metrics["weak_count"]} big topic gap{"s" if metrics["weak_count"] != 1 else ""} '
                      "flagged for revision")
    else:
        health_metric = "SET A TARGET"
        health_sub = "Enroll below and set targets to track goal health"

    if metrics["pending_items"]:
        exam_metric = f'{len(metrics["pending_items"])} PENDING'
        exam_sub = "Next up: " + ", ".join(metrics["pending_items"][:3])
    elif enrolled_count > 0:
        exam_metric = "ALL GRADED"
        exam_sub = "Every CIA and ESE paper has scores recorded"
    else:
        exam_metric = "NO EXAMS YET"
        exam_sub = "Enroll in a subject to view upcoming papers"

    components.render(
        '<div class="gl-mini-stack">'
        + components.home_mini_card(
            ("GOAL", "HEALTH"), health_metric, health_sub, components.ICON_HEART, "#F27D65")
        + components.home_mini_card(
            ("EXAM", "UPDATES"), exam_metric, exam_sub, components.ICON_CLOUD, "#43A854")
        + '</div>'
    )

with r2_right, components.card("home_line"):
    components.render(
        '<div class="gl-panel-label">PERCENTAGE'
        '<span>Topic score trend across CIAs</span></div>')
    if metrics["topic_labels"]:
        st.plotly_chart(
            plotly_theme.home_percentage_figure(
                metrics["topic_labels"], metrics["topic_pcts"], metrics["topic_details"]),
            key="home_percentage_chart",
            config={"displayModeBar": False},
        )
    else:
        components.render(components.empty_state(
            "No topic scores yet",
            "Enroll in a subject and once CIA marks are entered, your topic trend appears here."))

st.write("")

# ===================== 5. ROW 3: CORAL ACTION CARD + MINT BAR CHART =====================
r3_left, r3_right = st.columns([1, 2.25], gap="medium")

active_subject = profile.current_subject(student)
with r3_left, components.card("home_action"):
    if active_subject is not None:
        action_sub = f'{active_subject["code"]} · {active_subject["name"]}'
    else:
        action_sub = "Enroll in a subject below to open its dashboard"
    components.render(components.home_action_card_top("QUICK ACTION", "UPDATES", action_sub))
    with st.container(key="home_action_btn"):
        if st.button("Open Dashboard", key="home_open_dashboard", type="primary",
                     disabled=active_subject is None, icon=":material/arrow_forward:",
                     icon_position="right"):
            st.switch_page("views/student_dashboard.py")

with r3_right, components.card("home_bars"):
    components.render(components.home_green_header(
        "ASSESSMENT SCORES",
        f'{metrics["graded_count"]} GRADED · % OF MAX' if metrics["graded_count"] else "WAITING FOR MARKS",
    ))
    if metrics["comp_labels"]:
        st.plotly_chart(
            plotly_theme.home_bar_figure(
                metrics["comp_labels"], metrics["comp_pcts"], metrics["comp_details"]),
            key="home_scores_bar_chart",
            config={"displayModeBar": False},
        )
    else:
        components.render(
            '<div style="padding:48px 24px;text-align:center;color:#262833;font-weight:600;">'
            'No CIA or ESE scores recorded yet. Enroll in a subject below to start tracking.'
            '</div>')

# ===================== 6. ROW 4: MY SUBJECTS ENROLLMENT & TARGETS =====================
components.render(components.section_head(
    "My subjects",
    f'{student["class_name"]} · Enroll and set your target mark (/100)',
))


def card_meta(enrolled: bool, target) -> str:
    if not enrolled:
        return "Not enrolled yet"
    return "Enrolled" + (f" · Target {target:g}" if target is not None else " · No target yet")


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
elif not filtered_subjects:
    st.info(f'No subjects or topics match "{search_query}". Try another term or clear the search.')

for row_start in range(0, len(filtered_subjects), 2):
    cols = st.columns(2, gap="medium")
    for offset, subject in enumerate(filtered_subjects[row_start:row_start + 2]):
        idx = row_start + offset
        enrollment = enrollments.get(subject["id"])
        enrolled = enrollment is not None
        target = enrollment["target"] if enrolled else None
        sid = subject["id"]
        with cols[offset]:
            with st.container(key=f"subjcard_{sid}"):
                components.render(components.subject_card(
                    subject, idx, topics_by_subject[sid], card_meta(enrolled, target)))
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
                            profile.select_subject(sid)  # open this subject's dashboard
                            st.switch_page("views/student_dashboard.py")
                    else:
                        c_btn.button("Enroll", key=f"enroll_{sid}", type="primary",
                                     icon=":material/add:", on_click=do_enroll,
                                     args=(sid, subject["name"], tkey))

components.render(components.callout(
    "Your target drives the status on each subject dashboard. "
    "You can change it any time before the ESE results are published."))
