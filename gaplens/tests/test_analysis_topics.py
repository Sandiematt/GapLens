"""Topic progress across CIAs and topic losses (weak-topic ranking)."""
import pandas as pd
import pytest

from core import analysis


def analysed(spec, me, others=((0,),), flagged=()):
    """spec: [(q_id, max, topic_id, topic)]; me: scores in order; others: score rows."""
    questions = pd.DataFrame([{"question_id": qid, "q_no": i, "topic_id": tid, "topic": t,
                               "max_marks": float(mx)}
                              for i, (qid, mx, tid, t) in enumerate(spec, start=1)])
    rows = [{"question_id": spec[i][0], "roll_no": "ME", "score": s} for i, s in enumerate(me)]
    for n, other in enumerate(others):
        rows += [{"question_id": spec[i][0], "roll_no": f"R{n}", "score": s}
                 for i, s in enumerate(other)]
    return analysis.analyse_paper(questions, pd.DataFrame(rows), "ME", set(flagged))


def test_topic_progress_long_form_in_component_order():
    cia1 = analysed([(1, 5, 7, "Recursion"), (2, 10, 7, "Recursion"), (3, 5, 8, "Arrays")],
                    [1, None, 5], others=[(0, 0, 0)])
    cia2 = analysed([(4, 10, 7, "Recursion")], [7], others=[(0,)])
    rows = analysis.topic_progress({"CIA-2": cia2, "CIA-1": cia1})
    assert list(rows.columns) == ["component", "topic_id", "topic", "pct"]
    got = {(r.component, r.topic): r.pct for r in rows.itertuples()}
    assert got == {("CIA-1", "Recursion"): pytest.approx(100 / 15),  # 1 of 15, blank = 0
                   ("CIA-1", "Arrays"): pytest.approx(100.0),
                   ("CIA-2", "Recursion"): pytest.approx(70.0)}
    assert list(rows["component"]) == ["CIA-1", "CIA-1", "CIA-2"]


def test_topic_progress_empty_and_untagged_questions_ignored():
    assert analysis.topic_progress({}).empty
    cia1 = analysed([(1, 5, None, None), (2, 5, 8, "Arrays")], [5, 1], others=[(0, 0)])
    rows = analysis.topic_progress({"CIA-1": cia1})
    assert list(rows["topic"]) == ["Arrays"]


def test_topic_losses_rank_by_marks_lost_and_skip_flagged_questions():
    cia1 = analysed([(1, 10, 7, "Recursion"), (2, 5, 8, "Arrays"), (3, 4, 9, "Stacks")],
                    [2, 1, 1], others=[(0, 0, 0)], flagged=[2])  # Arrays Q is flagged
    cia2 = analysed([(4, 10, 7, "Recursion"), (5, 6, 9, "Stacks")], [6, None],
                    others=[(0, 0)])
    rows = analysis.topic_losses([cia1.table, cia2.table])
    assert list(rows.columns) == ["topic_id", "topic", "lost", "max", "lost_pct"]
    assert list(rows["topic"]) == ["Recursion", "Stacks"]  # Arrays only had a flagged Q
    rec, stk = rows.iloc[0], rows.iloc[1]
    assert (rec["lost"], rec["max"], rec["lost_pct"]) == (12, 20, pytest.approx(60.0))
    assert (stk["lost"], stk["max"], stk["lost_pct"]) == (9, 10, pytest.approx(90.0))


def test_topic_losses_groups_by_topic_id_not_title():
    a = analysed([(1, 10, 7, "Intro"), (2, 10, 8, "Intro")], [0, 5], others=[(0, 0)])
    rows = analysis.topic_losses([a.table])
    assert list(rows["topic_id"]) == [7, 8] and list(rows["lost"]) == [10, 5]


def test_topic_losses_empty():
    assert analysis.topic_losses([]).empty


# --- topic trends (Progress tab) -----------------------------------------------
def progress_rows(rows):
    return pd.DataFrame(rows, columns=["component", "topic_id", "topic", "pct"])


def test_topic_trends_rank_biggest_gain_first_and_need_two_papers():
    rows = progress_rows([("CIA-1", 7, "Recursion", 13.0), ("CIA-1", 8, "Arrays", 80.0),
                          ("CIA-1", 9, "Stacks", 50.0), ("CIA-2", 7, "Recursion", 70.0),
                          ("CIA-2", 8, "Arrays", 60.0), ("CIA-3", 8, "Arrays", 78.0)])
    trends = analysis.topic_trends(rows)
    assert list(trends.columns) == ["topic_id", "topic", "first", "last", "delta", "direction"]
    assert list(trends["topic"]) == ["Recursion", "Arrays"]  # Stacks is in one paper only
    assert trends.iloc[0][["first", "last", "delta"]].tolist() == [13, 70, 57]
    assert trends.iloc[1]["first"] == 80 and trends.iloc[1]["last"] == 78  # first vs last paper
    lines = analysis.trend_lines(rows)
    assert list(zip(lines["topic"], lines["component"])) == [
        ("Recursion", "CIA-1"), ("Recursion", "CIA-2"),
        ("Arrays", "CIA-1"), ("Arrays", "CIA-2"), ("Arrays", "CIA-3")]


def test_topic_trends_empty_when_no_topic_repeats():
    rows = progress_rows([("CIA-1", 7, "Recursion", 13.0), ("CIA-2", 8, "Arrays", 60.0)])
    assert analysis.topic_trends(rows).empty and analysis.trend_lines(rows).empty
    assert analysis.topic_trends(progress_rows([])).empty


def test_trend_direction_uses_the_config_threshold(monkeypatch):
    p = analysis.config.PROGRESS_TREND_POINTS
    assert analysis.trend_direction(50, 50 + p + 1) == analysis.TREND_UP
    assert analysis.trend_direction(50, 50 - p - 1) == analysis.TREND_DOWN
    assert analysis.trend_direction(50, 50 + p) == analysis.TREND_FLAT
    monkeypatch.setattr(analysis.config, "PROGRESS_TREND_POINTS", 20)
    assert analysis.trend_direction(50, 60) == analysis.TREND_FLAT
