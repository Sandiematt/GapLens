"""Seeded demo papers and marks, read back through the storage layer."""
import pytest

from core import db, seed


@pytest.fixture
def seeded(tmp_db):
    seed.ensure_seeded()
    subjects = {s["code"]: s["id"] for s in db.list_subjects()}
    return subjects


def paper(sid, comp):
    topics = {t["id"]: t["title"] for t in db.list_topics(sid)}
    return [(q["max_marks"], topics[q["topic_id"]]) for q in db.list_questions(sid, comp)]


def score(sid, comp, q_no, roll):
    q = next(q for q in db.list_questions(sid, comp) if q["q_no"] == q_no)
    return next(m["score"] for m in db.list_marks(sid, comp)
                if m["question_id"] == q["id"] and m["roll_no"] == roll)


def test_papers_match_spec(seeded):
    ds, py = seeded["MCA231"], seeded["MCA232"]
    assert paper(ds, "CIA-1") == [(2, "Arrays"), (3, "Time complexity"), (5, "Recursion"),
                                  (5, "Linked lists"), (10, "Recursion")]
    assert [m for m, _ in paper(ds, "CIA-2")] == [2, 2, 3, 3, 10, 10, 10, 10]
    assert paper(ds, "CIA-2")[6] == (10, "Recursion")
    assert paper(ds, "CIA-3") == [(5, "Sorting"), (5, "Hashing"), (5, "Binary search trees"),
                                  (10, "Graph traversal")]
    assert paper(py, "CIA-1")[4] == (10, "Lists and tuples")
    assert sum(m for m, _ in paper(py, "CIA-2")) == 50
    assert db.list_questions(py, "CIA-3") == []


def test_every_student_has_marks_and_ese_only_for_ds(seeded):
    ds, py = seeded["MCA231"], seeded["MCA232"]
    for comp, n in (("CIA-1", 5), ("CIA-2", 8), ("CIA-3", 4)):
        assert len(db.list_marks(ds, comp)) == 40 * n
    assert len(db.list_marks(py, "CIA-1")) == 200 and len(db.list_marks(py, "CIA-2")) == 280
    ese = db.list_ese_marks(ds)
    assert len(ese) == 40 and all(10 <= e["score"] <= 98 for e in ese if e["roll_no"] != "25MCA007")
    assert db.list_ese_marks(py) == []


def test_scores_within_max_and_half_marks(seeded):
    for sid in seeded.values():
        for comp in ("CIA-1", "CIA-2", "CIA-3"):
            mx = {q["id"]: q["max_marks"] for q in db.list_questions(sid, comp)}
            for m in db.list_marks(sid, comp):
                if m["score"] is not None:
                    assert 0 <= m["score"] <= mx[m["question_id"]]
                    assert m["score"] * 2 == int(m["score"] * 2)


def test_demo_student_overrides(seeded):
    ds, py, r = seeded["MCA231"], seeded["MCA232"], "25MCA007"
    assert [score(ds, "CIA-1", q, r) for q in (1, 3, 5)] == [0.5, 0.5, 1.5]
    assert score(ds, "CIA-2", 7, r) == 7
    assert [score(py, "CIA-1", q, r) for q in (1, 2, 3, 4, 5)] == [2, 3, 4.5, 2, 3]
    assert score(py, "CIA-2", 5, r) is None
    assert score(py, "CIA-2", 6, r) == 4
    ese = {e["roll_no"]: e["score"] for e in db.list_ese_marks(ds)}
    assert ese[r] == 58 and ese["25MCA012"] == 34


def test_seed_is_deterministic(tmp_db, tmp_path, monkeypatch):
    seed.ensure_seeded()
    first = [db.list_marks(s["id"], "CIA-2") for s in db.list_subjects()]
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "second.db")
    seed.ensure_seeded()
    assert first == [db.list_marks(s["id"], "CIA-2") for s in db.list_subjects()]
