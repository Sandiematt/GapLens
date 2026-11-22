"""Storage behaviour for papers, marks and ESE marks (temp SQLite)."""
import pytest

from core import db


@pytest.fixture
def subj(tmp_db):
    db.init_db()
    fid = db.add_faculty("F")
    sid = db.create_subject_with_topics(fid, "X1", "X", "C", 0.5, [(1, "A"), (1, "B")])
    topics = {t["title"]: t["id"] for t in db.list_topics(sid)}
    return sid, topics


def paper(topics, *spec):
    return [{"q_no": i, "max_marks": m, "topic_id": topics.get(t)}
            for i, (m, t) in enumerate(spec, start=1)]


def qids(sid, comp="CIA-1"):
    return {q["q_no"]: q["id"] for q in db.list_questions(sid, comp)}


def test_save_paper_keeps_marks_for_surviving_questions_and_drops_removed(subj):
    sid, topics = subj
    db.save_paper(sid, "CIA-1", paper(topics, (5, "A"), (10, "B"), (10, "A")))
    q = qids(sid)
    db.save_marks(sid, "CIA-1", [(q[1], "R1", 4.0), (q[2], "R1", None), (q[3], "R1", 7.0)])
    # edit Q1's max and topic, drop Q3
    db.save_paper(sid, "CIA-1", paper(topics, (6, "B"), (10, "B")))
    assert qids(sid) == {1: q[1], 2: q[2]}  # same ids: updated in place
    marks = {(m["question_id"], m["score"]) for m in db.list_marks(sid, "CIA-1")}
    assert marks == {(q[1], 4.0), (q[2], None)}
    assert db.list_questions(sid, "CIA-1")[0]["topic_id"] == topics["B"]


def test_save_marks_replaces_all_and_null_differs_from_zero(subj):
    sid, topics = subj
    db.save_paper(sid, "CIA-1", paper(topics, (5, "A"), (5, "A")))
    q = qids(sid)
    db.save_marks(sid, "CIA-1", [(q[1], "R1", 0.0), (q[2], "R1", None), (q[1], "R2", 3.0)])
    db.save_marks(sid, "CIA-1", [(q[1], "R1", 0.0), (q[2], "R1", None)])
    got = {(m["roll_no"], m["question_id"]): m["score"] for m in db.list_marks(sid, "CIA-1")}
    assert got == {("R1", q[1]): 0.0, ("R1", q[2]): None}


def test_marks_are_per_component(subj):
    sid, topics = subj
    db.save_paper(sid, "CIA-1", paper(topics, (5, "A")))
    db.save_paper(sid, "CIA-2", paper(topics, (5, "A")))
    db.save_marks(sid, "CIA-1", [(qids(sid)[1], "R1", 1.0)])
    db.save_marks(sid, "CIA-2", [(qids(sid, "CIA-2")[1], "R1", 2.0)])
    db.save_marks(sid, "CIA-1", [])
    assert db.list_marks(sid, "CIA-1") == [] and len(db.list_marks(sid, "CIA-2")) == 1


def test_deleting_a_topic_untags_questions_and_subject_delete_cascades(subj):
    sid, topics = subj
    db.save_paper(sid, "CIA-1", paper(topics, (5, "A")))
    q = qids(sid)[1]
    db.save_marks(sid, "CIA-1", [(q, "R1", 1.0)])
    db.update_topics(sid, [{"id": topics["B"], "unit_no": 1, "title": "B"}])
    assert db.list_questions(sid, "CIA-1")[0]["topic_id"] is None
    db.save_ese_marks(sid, [("R1", 50.0)])
    with db.transaction() as c:
        c.execute("DELETE FROM subjects WHERE id = ?", (sid,))
    with db.transaction() as c:
        for t in ("questions", "marks", "ese_marks"):
            assert c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0


def test_ese_marks_replace_all(subj):
    sid, _ = subj
    db.save_ese_marks(sid, [("R1", 50.0), ("R2", 33.5)])
    db.save_ese_marks(sid, [("R1", 61.0)])
    assert db.list_ese_marks(sid) == [{"roll_no": "R1", "score": 61.0}]


def test_questions_unique_per_component_number(subj):
    sid, _ = subj
    with db.transaction() as c:
        c.execute("INSERT INTO questions (subject_id, component, q_no, max_marks) "
                  "VALUES (?, 'CIA-1', 1, 5)", (sid,))
        with pytest.raises(Exception):
            c.execute("INSERT INTO questions (subject_id, component, q_no, max_marks) "
                      "VALUES (?, 'CIA-1', 1, 5)", (sid,))
