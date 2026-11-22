import pytest

import config
from core import db, seed


@pytest.fixture
def seeded(tmp_db):
    assert seed.ensure_seeded() is True
    return tmp_db


def topics_by_unit(code):
    subj = next(s for s in db.list_subjects(config.DEMO_CLASS) if s["code"] == code)
    out = {}
    for t in db.list_topics(subj["id"]):
        out.setdefault(t["unit_no"], []).append(t["title"])
    return out


def test_first_run_seeds_and_second_run_reuses(seeded):
    assert seed.ensure_seeded() is False
    assert len(db.list_students()) == 40
    assert len(db.list_faculty()) == 1


def test_seed_people(seeded):
    students = db.list_students(config.DEMO_CLASS)
    assert students[0]["roll_no"] == "25MCA001" and students[-1]["roll_no"] == "25MCA040"
    demo = db.get_student_by_roll("25MCA007")
    assert demo["name"] == "Demo Student"
    assert db.get_student_by_roll("25MCA008")["name"] == "Student 08"
    assert db.list_faculty()[0]["name"] == "Dr. Demo Faculty"


def test_seed_subjects_and_topics(seeded):
    assert topics_by_unit("MCA231") == seed.DS_UNITS
    assert topics_by_unit("MCA232") == seed.PY_UNITS
    ds = next(s for s in db.list_subjects() if s["code"] == "MCA231")
    py = next(s for s in db.list_subjects() if s["code"] == "MCA232")
    assert len(db.list_topics(ds["id"])) == 12
    assert len(db.list_topics(py["id"])) == 9
    assert ds["name"] == "Data Structures" and ds["cia_weight"] == 0.5


def test_seed_enrollments_and_targets(seeded):
    demo = db.get_student_by_roll("25MCA007")
    by_code = {s["code"]: s["id"] for s in db.list_subjects()}
    assert db.get_enrollment(demo["id"], by_code["MCA231"])["target"] == 80
    assert db.get_enrollment(demo["id"], by_code["MCA232"])["target"] == 75
    for sid in by_code.values():
        enrolled = db.list_subject_enrollments(sid)
        assert len(enrolled) == 40
        assert all(e["target"] in config.TARGET_CHOICES for e in enrolled
                   if e["roll_no"] != "25MCA007")


def test_seed_is_deterministic(tmp_path, monkeypatch):
    def targets(name):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / name)
        seed.ensure_seeded()
        sid = db.list_subjects()[0]["id"]
        return [e["target"] for e in db.list_subject_enrollments(sid)]

    assert targets("a.db") == targets("b.db")


def test_duplicate_roll_number_rejected(seeded):
    with pytest.raises(db.DuplicateError):
        db.add_student("25mca007", "Someone Else", "MCA-A")
    db.add_student("25MCA041", "New Kid", "MCA-A")
    assert len(db.list_students()) == 41


def test_subjects_filtered_by_class(seeded):
    assert len(db.list_subjects("MCA-A")) == 2
    assert db.list_subjects("MCA-B") == []


def test_enroll_and_target_validation(seeded):
    sid = db.list_subjects()[0]["id"]
    new = db.add_student("25MCA050", "Fresh", "MCA-A")
    assert db.get_enrollment(new, sid) is None
    db.enroll(new, sid)
    assert db.get_enrollment(new, sid)["target"] is None
    db.set_target(new, sid, 0)
    db.set_target(new, sid, 100)
    assert db.get_enrollment(new, sid)["target"] == 100
    for bad in (-1, 101):
        with pytest.raises(ValueError):
            db.set_target(new, sid, bad)
    db.enroll(new, sid)  # idempotent, keeps target
    assert db.get_enrollment(new, sid)["target"] == 100
    other = db.list_subjects()[1]["id"]
    with pytest.raises(ValueError):
        db.set_target(new, other, 50)  # not enrolled


def test_reset_restores_seeded_state(seeded):
    new = db.add_student("25MCA099", "Temp", "MCA-A")
    db.add_faculty("Another Faculty")
    sid = db.list_subjects()[0]["id"]
    demo = db.get_student_by_roll("25MCA007")
    db.set_target(demo["id"], sid, 61)
    seed.reset_demo()
    assert db.get_student_by_roll("25MCA099") is None
    assert len(db.list_students()) == 40
    assert len(db.list_faculty()) == 1
    demo = db.get_student_by_roll("25MCA007")
    sid = next(s["id"] for s in db.list_subjects() if s["code"] == "MCA231")
    assert db.get_enrollment(demo["id"], sid)["target"] == 80


def test_deleting_subject_cascades(seeded):
    sid = db.list_subjects()[0]["id"]
    with db.transaction() as conn:
        conn.execute("DELETE FROM subjects WHERE id = ?", (sid,))
    assert db.list_topics(sid) == []
    assert db.list_subject_enrollments(sid) == []
