"""Thin layer combining db and analysis for the pages."""
from __future__ import annotations

import config
from core import db


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
