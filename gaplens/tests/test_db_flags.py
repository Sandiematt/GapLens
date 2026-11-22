"""Silly-error flags: set, clear, per-subject lookup, per-question counts, cascades."""
import pytest

from core import db


@pytest.fixture
def setup(tmp_db):
    db.init_db()
    fid = db.add_faculty("F")
    s1 = db.create_subject_with_topics(fid, "X1", "X", "C", 0.5, [(1, "A")])
    s2 = db.create_subject_with_topics(fid, "X2", "Y", "C", 0.5, [(1, "A")])
    for sid in (s1, s2):
        db.save_paper(sid, "CIA-1", [{"q_no": 1, "max_marks": 5, "topic_id": None},
                                     {"q_no": 2, "max_marks": 5, "topic_id": None}])
    a, b = db.add_student("R1", "A", "C"), db.add_student("R2", "B", "C")
    q1 = {q["q_no"]: q["id"] for q in db.list_questions(s1, "CIA-1")}
    q2 = {q["q_no"]: q["id"] for q in db.list_questions(s2, "CIA-1")}
    return s1, s2, a, b, q1, q2


def test_set_is_idempotent_and_scoped_to_subject(setup):
    s1, s2, a, b, q1, q2 = setup
    db.set_silly_flag(a, q1[1])
    db.set_silly_flag(a, q1[1])
    db.set_silly_flag(a, q2[2])
    assert db.get_silly_flags(a, s1) == {q1[1]}
    assert db.get_silly_flags(a, s2) == {q2[2]}
    assert db.get_silly_flags(b, s1) == set()


def test_clear_removes_only_that_flag(setup):
    s1, _s2, a, _b, q1, _q2 = setup
    db.set_silly_flag(a, q1[1])
    db.set_silly_flag(a, q1[2])
    db.clear_silly_flag(a, q1[1])
    db.clear_silly_flag(a, q1[1])  # clearing again is harmless
    assert db.get_silly_flags(a, s1) == {q1[2]}


def test_counts_per_question_include_zero(setup):
    s1, _s2, a, b, q1, _q2 = setup
    db.set_silly_flag(a, q1[2])
    db.set_silly_flag(b, q1[2])
    assert db.count_silly_flags(s1, "CIA-1") == [
        {"question_id": q1[1], "q_no": 1, "flags": 0},
        {"question_id": q1[2], "q_no": 2, "flags": 2}]


def test_flags_cascade_with_questions_and_students(setup):
    s1, _s2, a, b, q1, _q2 = setup
    db.set_silly_flag(a, q1[1])
    db.set_silly_flag(b, q1[2])
    db.save_paper(s1, "CIA-1", [{"q_no": 2, "max_marks": 5, "topic_id": None}])  # drop Q1
    assert db.get_silly_flags(a, s1) == set()
    with db.transaction() as conn:
        conn.execute("DELETE FROM students WHERE id = ?", (b,))
    assert db.count_silly_flags(s1, "CIA-1")[0]["flags"] == 0
