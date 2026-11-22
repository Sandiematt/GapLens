"""Pure suggestion templates (no I/O, no Streamlit).

``question_tip`` turns one row of a paper analysis table into a concrete,
fact-based tip that names the topic, the max marks, the student's score,
the topper's score and the class average.
"""
from __future__ import annotations

import math
from urllib.parse import quote_plus

import config


def _num(x) -> float | None:
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


def fmt(x: float) -> str:
    """1 decimal place, trailing zeros dropped: 4.0 -> '4', 2.37 -> '2.4'."""
    return f"{x:.1f}".rstrip("0").rstrip(".")


def _marks(x: float) -> str:
    return f"{fmt(x)} mark" + ("" if abs(x - 1) < 1e-9 else "s")


def _topic(row) -> str:
    t = row.get("topic")
    return t if isinstance(t, str) and t.strip() else "this topic"


def _score(row) -> float:
    s = None if row.get("blank") else _num(row.get("score"))
    return s or 0.0


def tip_title(row) -> str:
    """'Q3 · Recursion · 5 marks'."""
    return f"Q{int(row['q_no'])} · {_topic(row)} · {_marks(float(row['max_marks']))}"


def potential_gain(row) -> float:
    """Marks still available on the question (blank = all of them)."""
    return float(row["max_marks"]) - _score(row)


def question_tip(row) -> str | None:
    """Templated suggestion for one analysed question, or None at full marks."""
    topic, mx = _topic(row), float(row["max_marks"])
    score, topper, avg = _score(row), float(row["topper"]), float(row["class_avg"])
    mistake = row["mistake_type"]
    facts = (f"You scored {fmt(score)} of {fmt(mx)}; the topper scored {fmt(topper)} "
             f"and the class averaged {fmt(avg)}.")

    if mistake == "Not attempted":
        return (f"You left this {fmt(mx)}-mark {topic} question blank, while the topper scored "
                f"{fmt(topper)} and the class averaged {fmt(avg)}. Next time write a partial "
                "answer: a definition, the key steps or a labelled diagram usually earns part marks.")
    if mistake == "Silly error flagged":
        return (f"{facts} You marked this as a calculation slip, so it is left out of your weak "
                f"topics. Re-check each step of {topic} answers before moving on, and keep the "
                "last five minutes of the paper for checking.")
    if mistake == "Silly loss":
        return (f"{facts} Most of the class did well on this {topic} question, so it is not a "
                "hard one: re-read the question and re-trace your working before writing the "
                "final answer.")
    if mistake == "Time pressure":
        return (f"{facts} This late question lost marks under time pressure. Budget time by "
                f"marks, answer the short questions first, and do one timed {fmt(mx)}-mark "
                f"{topic} question each day this week.")
    if mistake == "Concept gap":
        return (f"{facts} Revise {topic} from the basics, then attempt two previous-year "
                f"{fmt(mx)}-mark {topic} questions.")

    # OK
    if score >= mx - 1e-9:
        return None
    if score < topper - 1e-9:
        return (f"{facts} {_marks(topper - score)} behind the topper on {topic}: full-mark "
                "answers add a definition, a worked example and a labelled diagram.")
    return (f"{facts} You matched the top score on {topic}, {_marks(mx - score)} short of full: "
            "add a definition, a worked example and a labelled diagram to close it.")


# --- resources (SAN-125) ---------------------------------------------------------
RESOURCE_TYPES = ("video", "reading", "practice", "course")
DIFFICULTIES = ("beginner", "intermediate", "advanced")
_BIG_GAP_ORDER = ("video", "reading", "course", "practice")
_SMALL_GAP_ORDER = ("practice", "video", "reading", "course")


def search_links(subject_name: str, topic: str) -> list[dict]:
    """Auto-suggested search pages (never invented direct URLs), URL-encoded."""
    base = f"{subject_name} {topic}".strip()
    yt = quote_plus(base)
    nptel = quote_plus(f"site:nptel.ac.in {base}")
    prac = quote_plus(f"{base} practice problems")
    return [
        {"kind": "youtube", "title": f"YouTube: {topic}",
         "url": f"https://www.youtube.com/results?search_query={yt}"},
        {"kind": "nptel", "title": f"NPTEL: {topic}",
         "url": f"https://www.google.com/search?q={nptel}"},
        {"kind": "practice", "title": f"Practice: {topic} problems",
         "url": f"https://www.google.com/search?q={prac}"},
    ]


def order_resources(resources: list[dict], lost_pct: float) -> list[dict]:
    """Big gap: video, reading, course, practice. Small gap: practice first.
    Within a type, beginner then intermediate then advanced."""
    order = _BIG_GAP_ORDER if lost_pct >= config.BIG_GAP_PCT else _SMALL_GAP_ORDER

    def key(r):
        t, d = r.get("rtype"), r.get("difficulty")
        return (order.index(t) if t in order else len(order),
                DIFFICULTIES.index(d) if d in DIFFICULTIES else len(DIFFICULTIES))
    return sorted(resources, key=key)  # stable


def validate_resource(title, link, topic_id, rtype="video", difficulty="beginner") -> list[str]:
    errors = []
    if topic_id is None:
        errors.append("Pick a topic.")
    if not (title or "").strip():
        errors.append("Title is required.")
    if not (link or "").strip().lower().startswith(("http://", "https://")):
        errors.append("Link must start with http:// or https://.")
    if rtype not in RESOURCE_TYPES:
        errors.append("Pick a valid type.")
    if difficulty not in DIFFICULTIES:
        errors.append("Pick a valid difficulty.")
    return errors


# --- ESE presentation checklist (SAN-127) ----------------------------------------
# (key, label, tip). The tip is shown when the answer is "no".
PRESENTATION_CHECKLIST: list[tuple[str, str, str]] = [
    ("legible", "Handwriting is legible",
     "Slow down on the key words and numbers. Write every answer as if a tired examiner "
     "must read it once; if they cannot read it, they cannot give the marks."),
    ("headings", "Headings and underlining",
     "Underline the heading or key term of each answer with a ruler, and underline final "
     "results, so the examiner finds your marks-earning points at a glance."),
    ("diagrams", "Diagrams are labelled",
     "Label every diagram (nodes, axes, arrows, pointers) and give it a one-line caption. "
     "An unlabelled figure often earns half marks or less."),
    ("order", "Answered in order and numbered",
     "Answer in paper order and write the question number in the margin. If you skip one, "
     "leave space and mark it so nothing is missed."),
    ("time", "Finished in time",
     "Budget about one minute per mark and note the clock at each section. Answer the "
     "short, sure questions first and leave 10 minutes at the end."),
    ("length", "Answer length matches the marks",
     "Aim for one distinct point per mark: 2 marks is 2 lines, 5 marks is about 5 points "
     "or half a page. Do not write a page for 2 marks."),
    ("examples", "Examples, code and derivations used",
     "Back each theory answer with a small example, code snippet or worked derivation. "
     "Show every step; method marks are given even when the final value is wrong."),
    ("margins", "Clean margins and spacing",
     "Leave a margin and a blank line between answers, and cross out with a single line. "
     "A tidy page reads as a confident, well-organised answer."),
]


def checklist_review(answers: dict[str, bool]) -> str:
    """Markdown review: 'Doing well' for each yes, 'Improve' with one tip per no."""
    good = [f"- {label}" for k, label, _t in PRESENTATION_CHECKLIST if answers.get(k)]
    fix = [f"- **{label}.** {tip}" for k, label, tip in PRESENTATION_CHECKLIST
           if not answers.get(k)]
    return ("**Doing well**\n" + ("\n".join(good) or "- Nothing ticked yet.")
            + "\n\n**Improve**\n" + ("\n".join(fix) or "- Nothing to fix. Keep it up."))


def split_review(markdown: str) -> tuple[str, str]:
    """(doing_well, improve) bodies of a review. Free text without the headings is all 'improve'."""
    text = (markdown or "").strip()
    if "**Doing well**" not in text and "**Improve**" not in text:
        return "", text
    head, _, improve = text.partition("**Improve**")
    return head.replace("**Doing well**", "").strip(), improve.strip()
