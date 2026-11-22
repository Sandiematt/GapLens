"""UI smoke tests (Streamlit AppTest) for both roles, against a temp DB."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import db, seed

APP = str(Path(__file__).resolve().parents[1] / "app.py")

PAGES = {
    "Student": ["views/student_subjects.py", "views/student_dashboard.py"],
    "Faculty": ["views/faculty_subjects.py", "views/faculty_papers.py", "views/faculty_ese.py",
                "views/faculty_resources.py", "views/faculty_insights.py"],
}


@pytest.fixture
def app(tmp_db):
    seed.ensure_seeded()
    return AppTest.from_file(APP, default_timeout=30)


def test_student_default_profile_and_subjects(app):
    app.run()
    assert not app.exception
    text = " ".join(m.value for m in app.markdown)
    assert "Data Structures" in text and "Python Programming" in text
    assert "Demo Student" in text and "25MCA007" in text
    assert app.number_input[0].value == 80 and app.number_input[1].value == 75


@pytest.mark.parametrize("role", ["Student", "Faculty"])
def test_every_page_renders(app, role):
    for script in PAGES[role]:
        at = AppTest.from_file(APP, default_timeout=30)
        at.session_state["active_role"] = role
        at.switch_page(script)
        at.run()
        assert not at.exception, script
        assert len(at.sidebar.get("page_link")) == len(PAGES[role])


def test_new_student_enrolls_and_saves_target(app):
    db.add_student("25MCA099", "Newbie", "MCA-A")
    app.run()
    new = db.get_student_by_roll("25MCA099")
    app.session_state["student_id"] = new["id"]
    app.run()
    assert not app.exception
    app.button(key="enroll_1").click().run()
    sid = db.list_subjects()[0]["id"]
    assert db.get_enrollment(new["id"], sid) is not None
    app.number_input[0].set_value(88)
    app.button(key="save_1").click().run()
    assert db.get_enrollment(new["id"], sid)["target"] == 88
    assert not app.exception


def test_duplicate_roll_shows_error(app):
    app.run()
    app.text_input[0].set_value("25MCA007")
    app.text_input[1].set_value("Clone")
    app.get("form_submit_button")[0].click().run()
    assert any("already exists" in e.value for e in app.error)


def test_faculty_reset_flow(app):
    app.session_state["active_role"] = "Faculty"
    app.run()
    demo_id = db.get_student_by_roll("25MCA007")["id"]
    sid = db.list_subjects()[0]["id"]
    db.set_target(demo_id, sid, 61)
    app.button(key="reset_start").click().run()
    assert any("restores the demo" in w.value for w in app.warning)
    app.button(key="reset_yes").click().run()
    assert not app.exception
    assert db.get_enrollment(db.get_student_by_roll("25MCA007")["id"], sid)["target"] == 80
