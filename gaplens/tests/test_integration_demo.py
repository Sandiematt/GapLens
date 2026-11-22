"""The viva safety net: seed into a temporary SQLite file, read through the insights layer,
and assert every demo fact the spec promises. No Streamlit, network or Gemini key."""
import pytest

import config
from core import analysis, db, insights, seed

DEMO, FAILING = config.DEMO_STUDENT_ROLL, "25MCA012"
LIVE_BADGES = {"On track", "Stretch", "At risk", "Out of reach"}


@pytest.fixture
def demo(tmp_db):
    seed.ensure_seeded()
    subjects = {s["code"]: s for s in db.list_subjects()}
    student_id = db.get_student_by_roll(DEMO)["id"]
    return subjects, student_id


def _analyses(demo, code):
    subjects, student_id = demo
    return insights.student_paper_analyses(subjects[code]["id"], DEMO, student_id)


def _mistake(paper, q_no):
    table = paper.table
    return table[table["q_no"] == q_no].iloc[0]["mistake_type"]


def test_ds_cia1_has_a_silly_loss_and_a_concept_gap(demo):
    cia1 = _analyses(demo, "MCA231")["CIA-1"]
    assert _mistake(cia1, 1) == "Silly loss"
    assert _mistake(cia1, 3) == "Concept gap"


def test_python_cia1_shows_time_pressure(demo):
    assert _analyses(demo, "MCA232")["CIA-1"].time_pressure


def test_python_cia2_q5_is_not_attempted(demo):
    assert _mistake(_analyses(demo, "MCA232")["CIA-2"], 5) == "Not attempted"


def test_ds_recursion_improves_from_cia1_to_cia2(demo):
    progress = analysis.topic_progress(_analyses(demo, "MCA231"))
    recursion = progress[progress["topic"] == "Recursion"].set_index("component")["pct"]
    assert recursion["CIA-2"] > recursion["CIA-1"]


def test_goal_statuses_are_computed_for_both_subjects(demo):
    subjects, _ = demo
    targets = {e["subject_id"]: e["target"] for e in db.list_enrollments(db.get_student_by_roll(DEMO)["id"])}
    status = {}
    for code, subject in subjects.items():
        scores = insights.student_component_scores(subject["id"], DEMO)
        status[code] = analysis.goal_status(targets[subject["id"]], scores, subject["cia_weight"]).status
    assert status["MCA232"] in LIVE_BADGES  # CIA-3 and ESE still to come: the calculator is live
    assert status["MCA231"] in ("Achieved", "Missed")  # everything is in


def test_class_overview_has_all_40_students(demo):
    subjects, _ = demo
    for subject in subjects.values():
        rows = insights.class_overview(subject["id"])
        assert len(rows) == config.DEMO_STUDENT_COUNT == 40
        assert len({r["roll"] for r in rows}) == 40


def test_25mca012_has_an_ese_below_the_pass_mark(demo):
    subjects, _ = demo
    ese = {r["roll_no"]: r["score"] for r in db.list_ese_marks(subjects["MCA231"]["id"])}
    assert ese[FAILING] < config.ESE_PASS_MARK
    scores = insights.student_component_scores(subjects["MCA231"]["id"], FAILING)
    assert scores["ESE"] < config.ESE_PASS_MARK
