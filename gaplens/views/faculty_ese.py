"""Faculty: ESE Scripts (upload a script, manual presentation checklist, review, publish)."""
from __future__ import annotations

import json
from html import escape

import streamlit as st

from core import db, suggestions
from ui import components, profile
from ui.flash import flash, show_flash

PRIVACY = ("Gemini's free tier may use uploaded content to improve Google's products — "
           "use sample or dummy scripts for demos")
faculty = profile.current_faculty()
components.render(components.page_header(
    "ESE scripts", "Upload a script, review its presentation and publish feedback to the student."))
if faculty is None:
    st.info("No faculty profile exists yet. Create one from the sidebar.")
    st.stop()
subjects = db.list_subjects(faculty_id=faculty["id"])
if not subjects:
    st.info("You have no subjects yet. Create one on the My Subjects page first.")
    st.stop()
show_flash()

dv = st.session_state.get("data_version", 0)
rv = st.session_state.get("ese_version", 0)  # bumped after saving a script (resets the uploader)

with components.card("ese_pick"):
    c1, c2 = st.columns(2, gap="medium")
    subject = c1.selectbox("Subject", subjects, key=f"ese_subject_{dv}",
                           format_func=lambda s: f'{s["code"]} {s["name"]}')
    sid = subject["id"]
    names = {s["roll_no"]: s["name"] for s in db.list_subject_enrollments(sid)}
    ese = {m["roll_no"]: m["score"] for m in db.list_ese_marks(sid)}
    rolls = sorted(set(names) | set(ese))
    if not rolls:
        st.info("No students are enrolled and no ESE marks exist for this subject yet.")
        st.stop()

    def _label(r: str) -> str:
        score = ese.get(r)
        return (f'{r} · {names.get(r, "Not enrolled")} · '
                f'{"ESE not entered" if score is None else f"ESE {score:g}/100"}')

    roll = c2.selectbox("Student", rolls, key=f"ese_student_{dv}_{sid}", format_func=_label)

ident = f"{dv}_{sid}_{roll}"
review = db.get_review(sid, roll) or {}
checklist = json.loads(review.get("checklist") or "{}")
text_key = f"ese_review_text_{ident}"

components.render(components.callout(PRIVACY))

left, right = st.columns(2, gap="medium")

# --- script upload ---------------------------------------------------------------
with left, components.card("ese_script"):
    st.markdown("### Answer script")
    if review.get("script_name"):
        st.caption(f'Stored script: {review["script_name"]}')
        full = db.get_review(sid, roll, with_script=True)
        st.download_button("Download stored script", full["script"], file_name=full["script_name"],
                           mime=full["script_mime"] or "application/octet-stream",
                           key=f"ese_dl_{ident}", icon=":material/download:")
    else:
        st.caption("No script uploaded yet.")
    up = st.file_uploader("Upload script (PDF or photo)", type=["pdf", "png", "jpg", "jpeg"],
                          key=f"ese_up_{ident}_{rv}")
    if st.button("Save script", key=f"ese_save_script_{ident}", icon=":material/save:",
                 disabled=up is None):
        db.upsert_review(sid, roll, script_name=up.name,
                         script_mime=up.type or "application/octet-stream", script=up.getvalue())
        st.session_state["ese_version"] = rv + 1
        flash(f"Saved {up.name} for {roll}.")
        st.rerun()
    # SAN-128 hook: enable this button (drop ``disabled``) and store the model output with
    # db.upsert_review(sid, roll, ai_review=...). The checklist and draft below stay as they are.
    st.button("Generate AI review", key=f"ese_ai_{ident}", disabled=True,
              icon=":material/auto_awesome:", help="Arrives in SAN-128")
    st.caption("Arrives in SAN-128")

# --- checklist -----------------------------------------------------------------------
with right, components.card("ese_checklist"):
    st.markdown("### Presentation checklist")
    st.caption("Tick what the script does well. Each unticked item becomes a tip.")
    cols = st.columns(2)
    for i, (key, label, _tip) in enumerate(suggestions.PRESENTATION_CHECKLIST):
        cols[i % 2].checkbox(label, value=bool(checklist.get(key)), key=f"ese_chk_{key}_{ident}")
    if st.button("Generate tips from checklist", key=f"ese_gen_{ident}", type="primary",
                 icon=":material/checklist:"):
        answers = {k: bool(st.session_state[f"ese_chk_{k}_{ident}"])
                   for k, _l, _t in suggestions.PRESENTATION_CHECKLIST}
        db.upsert_review(sid, roll, checklist=json.dumps(answers),
                         final_review=suggestions.checklist_review(answers), published=False)
        st.session_state.pop(text_key, None)
        flash("Review drafted from the checklist. Edit it, then publish.")
        st.rerun()

# --- review editor ---------------------------------------------------------------------
published = bool(review.get("published"))
with components.card("ese_review"):
    head, pill_col = st.columns([4, 1], vertical_alignment="center")
    head.markdown("### Review for the student")
    pill_col.markdown(components.pill("Published" if published else "Draft",
                                      "ok" if published else "stretch"), unsafe_allow_html=True)
    text = st.text_area("Review text (markdown)", value=review.get("final_review") or "",
                        key=text_key, height=260)
    st.caption("Saving a draft takes the review off the student's page until you publish again.")
    b1, b2, b3, _ = st.columns([1, 1, 1, 3])
    if b1.button("Save draft", key=f"ese_savedraft_{ident}", icon=":material/save:"):
        db.upsert_review(sid, roll, final_review=text, published=False)
        flash("Draft saved.")
        st.rerun()
    if b2.button("Publish", key=f"ese_publish_{ident}", type="primary", icon=":material/publish:"):
        if not text.strip():
            st.error("Write or generate a review before publishing.")
        else:
            db.upsert_review(sid, roll, final_review=text, published=True)
            flash(f"Published the review to {roll}.")
            st.rerun()
    if b3.button("Unpublish", key=f"ese_unpublish_{ident}", disabled=not published,
                 icon=":material/visibility_off:"):
        db.upsert_review(sid, roll, published=False)
        flash("Unpublished. The student no longer sees it.")
        st.rerun()

# --- status table -------------------------------------------------------------------------
status = {s["roll_no"]: s for s in db.list_review_status(sid)}


def _yes(flag: bool) -> str:
    return components.pill("Yes", "ok") if flag else components.pill("No", "not-attempted")


rows = "".join(
    f'<tr><td>{escape(r)}</td><td>{escape(names.get(r, "Not enrolled"))}</td>'
    f'<td>{_yes(status.get(r, {}).get("has_script", False))}</td>'
    f'<td>{_yes(status.get(r, {}).get("has_review", False))}</td>'
    f'<td>{_yes(status.get(r, {}).get("published", False))}</td></tr>' for r in rolls)
with components.card("ese_status"):
    st.markdown(f"### Status · {subject['code']}")
    components.render(
        '<table class="gl-table"><thead><tr><th>Roll</th><th>Name</th><th>Script uploaded</th>'
        f'<th>Review written</th><th>Published</th></tr></thead><tbody>{rows}</tbody></table>')
