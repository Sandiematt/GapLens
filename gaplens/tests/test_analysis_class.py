"""Class-level analysis: question matrix, topic percentages, early-warning reasons."""
import pandas as pd
import pytest

from core import analysis


def frames(spec, scores):
    """spec: [(q_id, max, topic_id, topic)]; scores: {roll: [score or None per question]}."""
    q = pd.DataFrame([{"question_id": qid, "q_no": i, "topic_id": tid, "topic": t, "max_marks": float(mx)}
                      for i, (qid, mx, tid, t) in enumerate(spec, start=1)])
    m = pd.DataFrame([{"question_id": spec[i][0], "roll_no": r, "score": s}
                      for r, row in scores.items() for i, s in enumerate(row)])
    return q, m


SPEC = [(1, 10, 7, "Recursion"), (2, 5, 8, "Arrays"), (3, 5, None, None)]


def test_matrix_is_roll_by_question_percent_with_blanks_as_zero():
    q, m = frames(SPEC, {"B": [5, None, 5], "A": [10, 4, 0]})
    got = analysis.class_question_matrix(q, m)
    assert list(got.columns) == ["Q1", "Q2", "Q3"]
    assert list(got.index) == ["A", "B"]
    assert got.loc["A"].tolist() == pytest.approx([100, 80, 0])
    assert got.loc["B"].tolist() == pytest.approx([50, 0, 100])


def test_matrix_missing_row_counts_as_zero_and_empty_input():
    q, m = frames(SPEC, {"A": [10, 4, 5], "B": [5, 5, 5]})
    m = m[~((m.roll_no == "B") & (m.question_id == 2))]
    assert analysis.class_question_matrix(q, m).loc["B", "Q2"] == 0
    assert analysis.class_question_matrix(q, m.iloc[0:0]).empty


def test_topic_pct_sorted_worst_first_ignoring_untagged():
    q, m = frames(SPEC, {"A": [10, 1, 0], "B": [6, 3, 5]})
    got = analysis.class_topic_pct([(q, m)])
    assert list(got.columns) == ["topic", "pct"]
    assert list(got["topic"]) == ["Arrays", "Recursion"]
    assert got["pct"].tolist() == pytest.approx([40.0, 80.0])  # 4/10, 16/20


def test_topic_pct_pools_papers_by_topic_id():
    q1, m1 = frames([(1, 10, 7, "Recursion")], {"A": [10], "B": [10]})
    q2, m2 = frames([(9, 10, 7, "Recursion"), (10, 10, 8, "Arrays")], {"A": [0, 5], "B": [0, 5]})
    got = analysis.class_topic_pct([(q1, m1), (q2, m2)]).set_index("topic")["pct"]
    assert got["Recursion"] == pytest.approx(50.0)
    assert got["Arrays"] == pytest.approx(50.0)


def test_topic_pct_empty():
    assert analysis.class_topic_pct([]).empty


def goal(status):
    return analysis.GoalResult(status, 0, 0, 0, None, None, None)


def test_early_warning_reasons():
    assert analysis.early_warning_reasons(70, goal("On track")) == []
    assert analysis.early_warning_reasons(None, goal("No data")) == []
    assert analysis.early_warning_reasons(35, goal("On track")) == ["CIA average below 40%"]
    assert analysis.early_warning_reasons(60, goal("At risk")) == ["At risk target"]
    assert analysis.early_warning_reasons(30, goal("Out of reach")) == [
        "CIA average below 40%", "Out of reach target"]
    assert analysis.early_warning_reasons(40, goal("Stretch")) == []
