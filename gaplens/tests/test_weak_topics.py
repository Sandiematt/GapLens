"""Seeded-DB integration and UI smoke tests for SAN-125."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import config
from core import db, insights, seed

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def seeded(tmp_db):
    seed.ensure_seeded()


def _rows(code):
    sid = [s for s in db.list_subjects() if s["code"] == code][0]["id"]
    student = db.get_student_by_roll(config.DEMO_STUDENT_ROLL)
    an = insights.student_paper_analyses(sid, student["roll_no"], student["id"])
    return sid, insights.weak_topic_rows(sid, an)


def test_demo_student_ds_weak_topics_include_recursion_with_verified_resource(seeded):
    _sid, rows = _rows("MCA231")
    top = rows[:config.TOP_WEAK_TOPICS]
    rec = [r for r in top if r["topic"] == "Recursion"]
    assert rec, [r["topic"] for r in top]
    assert any("visualgo.net/en/recursion" in r["link"] for r in rec[0]["resources"])
    assert all(r["lost"] > 0 for r in rows)


def test_added_resource_appears_and_deleted_disappears(seeded):
    sid, rows = _rows("MCA231")
    topic_id = int([r for r in rows if r["topic"] == "Recursion"][0]["topic_id"])
    rid = db.add_resource(sid, topic_id, "Extra", "https://example.org/x", "video", "beginner", "5 min")
    _sid, rows = _rows("MCA231")
    assert "Extra" in [r["title"] for r in [r for r in rows if r["topic"] == "Recursion"][0]["resources"]]
    db.delete_resource(rid)
    _sid, rows = _rows("MCA231")
    assert "Extra" not in [r["title"] for r in [r for r in rows if r["topic"] == "Recursion"][0]["resources"]]


def test_resources_cascade_with_topic(seeded):
    sid, _ = _rows("MCA231")
    tid = [t for t in db.list_topics(sid) if t["title"] == "Recursion"][0]["id"]
    assert db.list_resources(sid, tid)
    db.update_topics(sid, [{"id": t["id"], "unit_no": t["unit_no"], "title": t["title"]}
                           for t in db.list_topics(sid) if t["id"] != tid])
    assert db.list_resources(sid, tid) == []


def _student_at(subject_index):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    code = ["MCA231", "MCA232"][subject_index]
    sub = [s for s in db.list_subjects() if s["code"] == code][0]
    at.session_state["subject_id"] = sub["id"]
    at.session_state["active_role"] = "Student"
    at.run()
    at.switch_page("views/student_dashboard.py")
    at.run()
    return at


@pytest.mark.parametrize("idx", [0, 1])
def test_student_weak_tab_renders_both_subjects(seeded, idx):
    at = _student_at(idx)
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Verified" in text and "Auto-suggested" in text and "Lost " in text


def _faculty():
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["active_role"] = "Faculty"
    at.run()
    at.switch_page("views/faculty_resources.py")
    at.run()
    return at


def test_faculty_adds_rejects_and_deletes(seeded):
    at = _faculty()
    assert not at.exception
    sid = at.selectbox[0].value
    before = len(db.list_resources(sid))
    at.text_input[0].set_value("My vid")
    at.text_input[1].set_value("youtube.com/x")
    at.get("form_submit_button")[0].click().run()
    assert any("http" in e.value for e in at.error)
    assert len(db.list_resources(sid)) == before
    at.text_input[1].set_value("https://youtu.be/abc")
    at.get("form_submit_button")[0].click().run()
    assert not at.exception and not at.error
    added = [r for r in db.list_resources(sid) if r["title"] == "My vid"]
    assert len(added) == 1
    at.button(key=f"del_res_{added[0]['id']}").click().run()
    assert not at.exception
    assert not [r for r in db.list_resources(sid) if r["title"] == "My vid"]
