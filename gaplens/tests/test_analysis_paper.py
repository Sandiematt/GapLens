"""Per-paper CIA analysis: totals, topper, percentile, mistake types, time pressure."""
import math

import pandas as pd
import pytest

from core import analysis


def paper(spec, marks):
    """spec: [(max_marks, topic)] in q_no order; marks: {roll: [score|None, ...]}."""
    questions = pd.DataFrame([
        {"question_id": 100 + i, "q_no": i, "topic_id": hash(t) % 1000 if t else None,
         "topic": t, "max_marks": float(mx)}
        for i, (mx, t) in enumerate(spec, start=1)])
    rows = [{"question_id": 100 + i, "roll_no": roll, "score": s}
            for roll, scores in marks.items() for i, s in enumerate(scores, start=1)]
    return questions, pd.DataFrame(rows, columns=["question_id", "roll_no", "score"])


def row(result, q_no):
    t = result.table
    return t[t["q_no"] == q_no].iloc[0]


# --- paper figures ------------------------------------------------------------
def test_no_marks_for_roll_returns_none():
    q, m = paper([(5, "A")], {"R1": [3]})
    assert analysis.analyse_paper(q, m, "NOBODY", set()) is None


def test_totals_topper_class_average_and_percentile():
    q, m = paper([(5, "A"), (5, "B")], {
        "ME": [3, 4],      # 7
        "R2": [5, 5],      # 10, topper
        "R3": [2, None],   # 2 (blank counts as 0)
        "R4": [4, 3],      # 7, tied with me
    })
    r = analysis.analyse_paper(q, m, "ME", set())
    assert r.total == 7 and r.max_total == 10
    assert r.topper_total == 10
    assert r.class_avg_total == pytest.approx(26 / 4)
    assert r.class_size == 4
    # one below (2), two tied at 7 including me: (1 + 0.5*2) / 4 * 100
    assert r.percentile == pytest.approx(50.0)


def test_unmatched_rolls_count_in_class_figures():
    q, m = paper([(10, "A")], {"ME": [5], "STRANGER": [9]})
    r = analysis.analyse_paper(q, m, "ME", set())
    assert r.topper_total == 9 and r.class_size == 2
    assert r.percentile == pytest.approx(25.0)  # 0 below, 1 tie (me) -> 0.5/2


def test_question_table_columns_and_values():
    q, m = paper([(4, "Arrays"), (6, "Stacks")], {
        "ME": [None, 3], "R2": [4, 6], "R3": [2, 0]})
    r = analysis.analyse_paper(q, m, "ME", set())
    assert list(r.table.columns) == [
        "question_id", "q_no", "topic_id", "topic", "max_marks", "score", "blank",
        "topper", "class_avg", "percentile", "mistake_type", "flagged"]
    q1, q2 = row(r, 1), row(r, 2)
    assert q1["blank"] and math.isnan(q1["score"])
    assert q1["topper"] == 4 and q1["class_avg"] == pytest.approx(2.0)
    assert q1["percentile"] == pytest.approx(100 * 0.5 / 3)  # blank = 0, ties with nobody
    assert not q2["blank"] and q2["score"] == 3
    assert q2["topper"] == 6 and q2["class_avg"] == pytest.approx(3.0)
    assert q2["percentile"] == pytest.approx(100 * 1.5 / 3)  # 1 below, 1 tie (me)


# --- mistake types and their order ---------------------------------------------
def one_question(me, others, mx=10, flagged=False):
    q, m = paper([(mx, "Topic")], {"ME": [me], **{f"R{i}": [s] for i, s in enumerate(others)}})
    r = analysis.analyse_paper(q, m, "ME", {101} if flagged else set())
    return row(r, 1)["mistake_type"]


def test_blank_is_not_attempted_even_when_flagged():
    assert one_question(None, [8, 8, 8], flagged=True) == "Not attempted"


def test_flag_beats_silly_loss():
    assert one_question(3, [10] * 7 + [0] * 2, flagged=True) == "Silly error flagged"


def test_flagged_full_question_reads_flagged():
    q, m = paper([(5, "A")], {"ME": [4], "R2": [5]})
    r = analysis.analyse_paper(q, m, "ME", {101})
    assert row(r, 1)["flagged"] and row(r, 1)["mistake_type"] == "Silly error flagged"


def test_silly_loss_when_70pct_of_class_scored_60pct_and_student_under_40pct():
    # 7 of 10 (incl. me) at >= 60%; class avg 4.9/10 so no concept gap either way
    assert one_question(3, [6] * 7 + [2, 2]) == "Silly loss"


def test_silly_loss_beats_concept_gap():
    assert one_question(3, [10] * 7 + [0, 0]) == "Silly loss"


def test_only_60pct_of_class_strong_is_concept_gap_not_silly_loss():
    assert one_question(3, [10] * 6 + [0, 0, 0]) == "Concept gap"


def test_student_at_40pct_is_not_a_silly_loss():
    # 4/10 is not under 40%; class avg 7.4 -> 0.4 <= 0.49, so concept gap
    assert one_question(4, [10] * 7 + [0, 0]) == "Concept gap"


def test_concept_gap_boundary_25_points_below_class_average():
    # class avg 7.5/10 = 0.75 in both: 0.50 is a gap (exactly 25 below), 0.55 is OK
    assert one_question(5, [10, 10, 5]) == "Concept gap"
    assert one_question(5.5, [10, 10, 4.5]) == "OK"


def test_ok_when_nothing_applies():
    assert one_question(8, [8, 9, 7]) == "OK"


# --- time pressure ------------------------------------------------------------
def three_q(me, others):
    q, m = paper([(10, "A"), (10, "B"), (10, "C")],
                 {"ME": me, **{f"R{i}": s for i, s in enumerate(others)}})
    return analysis.analyse_paper(q, m, "ME", set())


def test_time_pressure_when_student_drops_far_more_than_class():
    r = three_q([10, 10, 4], [[8, 8, 8]] * 3)
    assert r.time_pressure
    assert r.student_drop == pytest.approx(60)
    assert r.class_drop == pytest.approx(15)  # 85% -> 70%
    # 0.4 vs class 0.7 is also a concept gap; time pressure is checked first
    assert row(r, 3)["mistake_type"] == "Time pressure"


def test_no_time_pressure_when_class_drops_just_as_much():
    r = three_q([10, 10, 6], [[10, 10, 6]] * 3)
    assert not r.time_pressure
    assert r.student_drop == pytest.approx(40) and r.class_drop == pytest.approx(40)
    assert row(r, 3)["mistake_type"] == "OK"


def test_time_pressure_boundaries_drop_20_and_excess_15_count():
    r = three_q([10, 10, 8], [[10, 10, 10]] * 3)
    assert r.student_drop == pytest.approx(20) and r.class_drop == pytest.approx(5)
    assert r.time_pressure


def test_no_time_pressure_when_excess_over_class_is_under_15():
    r = three_q([10, 10, 8], [[10, 10, 9.5]] * 3)
    assert r.student_drop == pytest.approx(20) and r.class_drop == pytest.approx(8.75)
    assert not r.time_pressure


def test_time_pressure_needs_three_questions():
    q, m = paper([(10, "A"), (10, "B")], {"ME": [10, 0], "R1": [10, 10]})
    r = analysis.analyse_paper(q, m, "ME", set())
    assert not r.time_pressure and r.student_drop is None and r.class_drop is None
    assert row(r, 2)["mistake_type"] == "Concept gap"


def test_last_third_rounds_up_and_needs_share_below_class_average():
    # 4 questions -> last ceil(4/3) = 2 are the last third
    q, m = paper([(10, "A")] * 4, {"ME": [10, 10, 4, 9],
                                   **{f"R{i}": [10, 10, 9, 9] for i in range(3)}})
    r = analysis.analyse_paper(q, m, "ME", set())
    assert r.time_pressure
    assert r.student_drop == pytest.approx(35) and r.class_drop == pytest.approx(16.25)
    assert row(r, 3)["mistake_type"] == "Time pressure"
    assert row(r, 4)["mistake_type"] == "OK"  # at the class average, not below


def test_first_part_question_is_never_time_pressure():
    q, m = paper([(10, "A")] * 3, {"ME": [2, 10, 4], "R0": [9, 9, 9], "R1": [9, 9, 9],
                                   "R2": [0, 9, 9]})
    r = analysis.analyse_paper(q, m, "ME", set())
    assert r.time_pressure  # me 60% -> 40%, class 71.25% -> 77.5%
    assert row(r, 1)["mistake_type"] == "Concept gap"
    assert row(r, 3)["mistake_type"] == "Time pressure"
