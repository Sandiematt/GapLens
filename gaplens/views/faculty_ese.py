"""Faculty: ESE Scripts (upload a script, manual presentation checklist, review, publish)."""
from __future__ import annotations

import json
from html import escape

import streamlit as st

import config
from core import db, gemini_client, suggestions
from ui import components, profile, secrets
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

data_version = st.session_state.get("data_version", 0)
ese_version = st.session_state.get("ese_version", 0)  # bumped after saving a script (resets the uploader)

with components.card("ese_pick"):
    c1, c2 = st.columns(2, gap="medium")
    subject = c1.selectbox("Subject", subjects, key=f"ese_subject_{data_version}",
                           format_func=lambda s: f'{s["code"]} {s["name"]}')
    sid = subject["id"]
    names = {s["roll_no"]: s["name"] for s in db.list_subject_enrollments(sid)}
    ese = {m["roll_no"]: m["score"] for m in db.list_ese_marks(sid)}
    rolls = sorted(set(names) | set(ese))
    if not rolls:
        st.info("No students are enrolled and no ESE marks exist for this subject yet.")
        st.stop()

    ese_max = config.COMPONENTS["ESE"]

    def _label(r: str) -> str:
        score = ese.get(r)
        mark = "ESE not entered" if score is None else f"ESE {score:g}/{ese_max}"
        return f'{r} · {names.get(r, "Not enrolled")} · {mark}'

    roll = c2.selectbox("Student", rolls, key=f"ese_student_{data_version}_{sid}", format_func=_label)

ident = f"{data_version}_{sid}_{roll}"
review = db.get_review(sid, roll) or {}
checklist = json.loads(review.get("checklist") or "{}")
text_key = f"ese_review_text_{ident}"

components.render(components.callout(PRIVACY))

left, right = st.columns(2, gap="medium")

# --- script upload ---------------------------------------------------------------
with left, components.card("ese_script"):
    components.render(components.card_title("Answer script"))
    full = db.get_review(sid, roll, with_script=True) if review.get("script_name") else None
    has_script = bool(full and full["script"])
    if has_script:
        size_mb = len(full["script"]) / (1024 * 1024)
        st.caption(f'Stored script: {review["script_name"]} · {size_mb:.1f} MB')
        st.download_button("Download stored script", full["script"], file_name=full["script_name"],
                           mime=full["script_mime"] or "application/octet-stream",
                           key=f"ese_dl_{ident}", icon=":material/download:")
        if size_mb > config.GEMINI_SCRIPT_WARN_MB:
            st.warning(f"This script is {size_mb:.0f} MB. Gemini may reject files this large; "
                       "upload a smaller scan, or use the manual checklist.")
    else:
        st.caption("No script uploaded yet.")
    up = st.file_uploader("Upload script (PDF or photo)", type=["pdf", "png", "jpg", "jpeg"],
                          key=f"ese_up_{ident}_{ese_version}")
    if st.button("Save script", key=f"ese_save_script_{ident}", icon=":material/save:",
                 disabled=up is None):
        db.upsert_review(sid, roll, script_name=up.name,
                         script_mime=up.type or "application/octet-stream", script=up.getvalue())
        st.session_state["ese_version"] = ese_version + 1
        flash(f"Saved {up.name} for {roll}.")
        st.rerun()
    gemini_key = secrets.get_gemini_key()
    if not gemini_key:
        ai_note = ("No Gemini API key is configured, so AI review is off. Use the presentation "
                   "checklist, or add GEMINI_API_KEY to .streamlit/secrets.toml.")
    elif not has_script:
        ai_note = "Save a script first, then Gemini can review its presentation."
    elif (review.get("ai_review") or "").strip():
        ai_note = "An AI draft is already saved. Generating again replaces the current draft."
    else:
        ai_note = "Gemini reviews presentation only. The result opens as a draft; it is never published automatically."
    if st.button("Generate AI review", key=f"ese_ai_{ident}", icon=":material/auto_awesome:",
                 disabled=not (gemini_key and has_script)):
        with st.spinner("Gemini is reviewing the script's presentation…"):
            try:
                ai_text = gemini_client.review_ese_script(
                    full["script"], gemini_client.guess_mime(full["script_name"], full["script_mime"]),
                    gemini_key, secrets.get_gemini_model())
            except gemini_client.GeminiError as exc:
                st.error(f"{exc} Use the manual checklist instead.")
            else:
                db.upsert_review(sid, roll, ai_review=ai_text, final_review=ai_text, published=False)
                st.session_state.pop(text_key, None)
                flash("AI review drafted. Check and edit it, then publish.")
                st.rerun()
    st.caption(ai_note)

# --- checklist -----------------------------------------------------------------------
with right, components.card("ese_checklist"):
    components.render(components.card_title(
        "Presentation checklist", "Tick what the script does well. Each unticked item becomes a tip."))
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
    components.render(components.card_title(
        "Review for the student",
        aside_html=components.pill("Published" if published else "Draft",
                                   "ok" if published else "stretch")))
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


rows = [[escape(r), escape(names.get(r, "Not enrolled")),
         _yes(status.get(r, {}).get("has_script", False)),
         _yes(status.get(r, {}).get("has_review", False)),
         _yes(status.get(r, {}).get("published", False))] for r in rolls]
with components.card("ese_status"):
    components.render(components.card_title(f"Status · {subject['code']}"))
    components.render(components.table(
        ["Roll", "Name", "Script uploaded", "Review written", "Published"], rows))
