"""Seeded DB -> insights -> analysis: the demo story for SAN-124."""
import pytest

from core import analysis, db, insights, seed

DEMO = "25MCA007"


@pytest.fixture
def demo(tmp_db):
    seed.ensure_seeded()
    subs = {s["code"]: s["id"] for s in db.list_subjects()}
    return subs, db.get_student_by_roll(DEMO)["id"]


def mistake(a, q_no):
    t = a.table
    return t[t["q_no"] == q_no].iloc[0]["mistake_type"]


def test_ds_cia1_shows_silly_loss_and_concept_gap(demo):
    subs, sid = demo
    a = insights.student_paper_analyses(subs["MCA231"], DEMO, sid)
    assert set(a) == {"CIA-1", "CIA-2", "CIA-3"}
    assert mistake(a["CIA-1"], 1) == "Silly loss"
    assert mistake(a["CIA-1"], 3) == "Concept gap"
    assert a["CIA-1"].class_size == 40


def test_python_cia1_time_pressure_and_cia2_blank(demo):
    subs, sid = demo
    a = insights.student_paper_analyses(subs["MCA232"], DEMO, sid)
    assert set(a) == {"CIA-1", "CIA-2"}  # no CIA-3 paper yet
    assert a["CIA-1"].time_pressure
    assert mistake(a["CIA-2"], 5) == "Not attempted"


def test_ds_recursion_improves_from_cia1_to_cia2(demo):
    subs, sid = demo
    rows = analysis.topic_progress(insights.student_paper_analyses(subs["MCA231"], DEMO, sid))
    rec = rows[rows["topic"] == "Recursion"].set_index("component")["pct"]
    assert rec["CIA-2"] > rec["CIA-1"]


def test_toggling_a_flag_changes_the_mistake_type(demo):
    subs, sid = demo
    ds = subs["MCA231"]
    q1 = insights.student_paper_analyses(ds, DEMO, sid)["CIA-1"].table.iloc[0]
    db.set_silly_flag(sid, int(q1["question_id"]))
    after = insights.student_paper_analyses(ds, DEMO, sid)["CIA-1"]
    assert mistake(after, 1) == "Silly error flagged"
    # Arrays is only asked in Q1, so the flag takes it out of the weak-topic ranking
    assert q1["topic"] == "Arrays"
    assert "Arrays" not in set(analysis.topic_losses([after.table])["topic"])
    db.clear_silly_flag(sid, int(q1["question_id"]))
    assert mistake(insights.student_paper_analyses(ds, DEMO, sid)["CIA-1"], 1) == "Silly loss"


def test_roll_without_marks_has_no_analyses(demo):
    subs, _sid = demo
    assert insights.student_paper_analyses(subs["MCA231"], "NOBODY", None) == {}
