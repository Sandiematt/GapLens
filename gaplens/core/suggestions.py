"""Pure suggestion templates (no I/O, no Streamlit).

``question_tip`` turns one row of a paper analysis table into a concrete,
fact-based tip that names the topic, the max marks, the student's score,
the topper's score and the class average.
"""
from __future__ import annotations

import math


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
