"""Thin layer combining db and analysis for the pages."""
from __future__ import annotations

import pandas as pd

import config
from core import analysis, db


def student_component_scores(subject_id: int, roll_no: str) -> dict[str, float | None]:
    """{component: total or None} for one roll.

    The total sums the roll's marks with blanks counted as 0. None means the
    roll has no marks for that paper (or no ESE total).
    """
    scores: dict[str, float | None] = {}
    for comp in config.CIA_COMPONENTS:
        rows = [m for m in db.list_marks(subject_id, comp) if m["roll_no"] == roll_no]
        scores[comp] = sum(m["score"] or 0 for m in rows) if rows else None
    ese = [r["score"] for r in db.list_ese_marks(subject_id) if r["roll_no"] == roll_no]
    scores["ESE"] = float(ese[0]) if ese and ese[0] is not None else None
    return scores


def paper_frames(subject_id: int, component: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(questions_df, marks_df) for one paper, in the shape analysis expects."""
    titles = {t["id"]: t["title"] for t in db.list_topics(subject_id)}
    questions = pd.DataFrame(
        [{"question_id": q["id"], "q_no": q["q_no"], "topic_id": q["topic_id"],
          "topic": titles.get(q["topic_id"]), "max_marks": q["max_marks"]}
         for q in db.list_questions(subject_id, component)],
        columns=["question_id", "q_no", "topic_id", "topic", "max_marks"])
    marks = pd.DataFrame(db.list_marks(subject_id, component),
                         columns=["question_id", "roll_no", "score"])
    return questions, marks


def student_paper_analyses(subject_id: int, roll_no: str,
                           student_id: int | None) -> dict[str, analysis.PaperAnalysis]:
    """{component: PaperAnalysis} for every CIA paper where the roll has marks.

    The student's silly-error flags are applied; ``student_id`` None means none.
    """
    flags = db.get_silly_flags(student_id, subject_id) if student_id is not None else set()
    result = {}
    for comp in config.CIA_COMPONENTS:
        questions, marks = paper_frames(subject_id, comp)
        a = analysis.analyse_paper(questions, marks, roll_no, flags)
        if a is not None:
            result[comp] = a
    return result


def weak_topic_rows(subject_id: int, analyses: dict[str, analysis.PaperAnalysis],
                    top_n: int | None = None) -> list[dict]:
    """Topics with marks lost (most first), each with its verified resources ordered for the gap."""
    from core import suggestions  # local: keeps module imports light
    losses = analysis.topic_losses([a.table for a in analyses.values()])
    losses = losses[losses["lost"] > 0]
    if top_n is not None:
        losses = losses.head(top_n)
    by_topic: dict[int, list[dict]] = {}
    for r in db.list_resources(subject_id):
        by_topic.setdefault(r["topic_id"], []).append(r)
    rows = []
    for rec in losses.to_dict("records"):
        rows.append({**rec, "resources": suggestions.order_resources(
            by_topic.get(int(rec["topic_id"]), []), rec["lost_pct"])})
    return rows
