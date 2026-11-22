import pytest

from core import analysis, db, insights, seed


@pytest.fixture
def seeded(tmp_db):
    seed.ensure_seeded()
    subs = {s["code"]: s for s in db.list_subjects()}
    return subs


def test_demo_student_scores_python_has_pending_components(seeded):
    s = insights.student_component_scores(seeded["MCA232"]["id"], "25MCA007")
    assert set(s) == {"CIA-1", "CIA-2", "CIA-3", "ESE"}
    assert s["CIA-1"] == 14.5  # 2+3+4.5+2+3
    assert s["CIA-2"] is not None and s["CIA-3"] is None and s["ESE"] is None
    g = analysis.goal_status(75, s, 0.5)
    assert g.required_pct is not None and g.status != "No data"


def test_demo_student_data_structures_is_complete(seeded):
    sid = seeded["MCA231"]["id"]
    s = insights.student_component_scores(sid, "25MCA007")
    assert s["ESE"] == 58 and all(v is not None for v in s.values())
    assert analysis.goal_status(80, s, 0.5).status in ("Achieved", "Missed")


def test_unknown_roll_has_no_data(seeded):
    s = insights.student_component_scores(seeded["MCA232"]["id"], "NEWROLL")
    assert s == {"CIA-1": None, "CIA-2": None, "CIA-3": None, "ESE": None}


def test_blank_scores_count_as_zero(seeded):
    sid = seeded["MCA232"]["id"]
    qs = db.list_questions(sid, "CIA-2")
    db.save_marks(sid, "CIA-2", [(q["id"], "R1", None) for q in qs])
    assert insights.student_component_scores(sid, "R1")["CIA-2"] == 0
