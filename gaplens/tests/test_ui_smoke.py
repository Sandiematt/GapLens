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
        at.run()  # switch_page is ignored before the first run
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


def _faculty_app(app):
    app.session_state["active_role"] = "Faculty"
    app.run()
    assert not app.exception
    return app


def test_faculty_creates_subject_and_students_see_it(app):
    _faculty_app(app)
    app.text_input[0].set_value("mca240")
    app.text_input[1].set_value("Networks")
    app.text_area[0].set_value("1 | OSI\nRouting\n2 | Transport")
    app.get("form_submit_button")[0].click().run()
    assert not app.exception and not app.error
    subj = [s for s in db.list_subjects(class_name="MCA-A") if s["code"] == "MCA240"][0]
    assert [(t["unit_no"], t["title"]) for t in db.list_topics(subj["id"])] == [
        (1, "OSI"), (1, "Routing"), (2, "Transport")]
    student = AppTest.from_file(APP, default_timeout=30)
    student.run()
    assert "Networks" in " ".join(m.value for m in student.markdown)


def test_faculty_create_validation_and_duplicate_errors(app):
    _faculty_app(app)
    app.get("form_submit_button")[0].click().run()
    assert len(app.error) >= 3
    app.text_input[0].set_value("MCA231")
    app.text_input[1].set_value("Dup")
    app.text_area[0].set_value("x")
    app.get("form_submit_button")[0].click().run()
    assert any("already exists" in e.value for e in app.error)
    assert len(db.list_subjects()) == 2


def test_faculty_sees_only_own_subjects(app):
    other = db.add_faculty("Someone Else")
    db.create_subject_with_topics(other, "ZZ1", "Hidden", "MCA-A", 0.5, [(1, "t")])
    _faculty_app(app)
    text = " ".join(m.value for m in app.markdown)
    assert "Data Structures" in text and "Hidden" not in text


def test_papers_page_components_and_double_save(app):
    _faculty_app(app)
    app.switch_page("views/faculty_papers.py")
    app.run()
    assert not app.exception
    ds = db.list_subjects()[0]["id"]
    before = (db.list_questions(ds, "CIA-1"), len(db.list_marks(ds, "CIA-1")))
    for _ in range(2):  # saving twice must not duplicate anything
        app.button(key="save_paper").click().run()
        assert not app.exception and not app.error
        app.button(key="save_marks").click().run()
        assert not app.exception and not app.error
    assert (db.list_questions(ds, "CIA-1"), len(db.list_marks(ds, "CIA-1"))) == before
    for comp in ("CIA-2", "CIA-3", "ESE"):
        app.selectbox[1].select(comp).run()
        assert not app.exception, comp
    app.button(key="save_ese").click().run()
    assert not app.exception and len(db.list_ese_marks(ds)) == 40
    app.selectbox[0].select_index(1).run()  # Python: no CIA-3 paper yet
    app.selectbox[1].select("CIA-3").run()
    assert not app.exception and any("Save the question paper first" in i.value for i in app.info)


# --- subject dashboard (SAN-123) ---------------------------------------------
def _dashboard(student_id=None, subject_id=None):
    at = AppTest.from_file(APP, default_timeout=30)
    if student_id:
        at.session_state["student_id"] = student_id
    if subject_id:
        at.session_state["selected_subject_id"] = subject_id
    at.run()  # switch_page is ignored before the first run
    at.switch_page("views/student_dashboard.py")
    at.run()
    return at


def _text(at):
    return " ".join(m.value for m in at.markdown)


def test_dashboard_demo_student_python_shows_required_pct(tmp_db):
    seed.ensure_seeded()
    py = [s for s in db.list_subjects() if s["code"] == "MCA232"][0]
    at = _dashboard(subject_id=py["id"])
    assert not at.exception
    text = _text(at)
    assert "You need an average of" in text and "CIA-3 and ESE" in text
    assert "Welcome back, Demo Student" in text
    assert {"Goal", "CIA Analysis", "Weak Topics & Resources", "Progress", "ESE"} <= {t.label for t in at.tabs}


def test_dashboard_demo_student_data_structures_shows_final(tmp_db):
    seed.ensure_seeded()
    ds = [s for s in db.list_subjects() if s["code"] == "MCA231"][0]
    at = _dashboard(subject_id=ds["id"])
    assert not at.exception
    text = _text(at)
    assert "Final mark" in text and ("Achieved" in text or "Missed" in text)


def test_dashboard_new_student_no_marks(tmp_db):
    seed.ensure_seeded()
    sid = db.add_student("25MCA099", "Newbie", "MCA-A")
    subject = db.list_subjects()[1]
    db.enroll(sid, subject["id"], 70)
    at = _dashboard(student_id=sid)
    assert not at.exception
    assert "Set \u2014 no data yet" in _text(at)


def test_dashboard_without_target_points_to_my_subjects(tmp_db):
    seed.ensure_seeded()
    sid = db.add_student("25MCA098", "Notarget", "MCA-A")
    db.enroll(sid, db.list_subjects()[0]["id"])
    at = _dashboard(student_id=sid)
    assert not at.exception
    assert "No target set" in _text(at)


def test_dashboard_not_enrolled(tmp_db):
    seed.ensure_seeded()
    sid = db.add_student("25MCA097", "Fresh", "MCA-A")
    at = _dashboard(student_id=sid)
    assert not at.exception and any("My Subjects" in i.value for i in at.info)


# --- CIA Analysis and Progress tabs (SAN-124) ----------------------------------
def _subject(code):
    return [s for s in db.list_subjects() if s["code"] == code][0]["id"]


def test_cia_and_progress_tabs_data_structures(tmp_db):
    seed.ensure_seeded()
    ds = _subject("MCA231")
    at = _dashboard(subject_id=ds)
    assert not at.exception
    text = _text(at)
    assert "CIA paper analysis" in text and "Class topper" in text
    assert "Silly loss" in text and "Concept gap" in text  # CIA-1 is shown first
    assert "Are your weak topics improving?" in text
    assert "Recursion: 13% → 70%" in text
    for comp in ("CIA-2", "CIA-3"):
        at.segmented_control(key=f"cia_paper_{ds}").set_value(comp).run()
        assert not at.exception, comp


def test_cia_and_progress_tabs_python(tmp_db):
    seed.ensure_seeded()
    py = _subject("MCA232")
    at = _dashboard(subject_id=py)
    assert not at.exception
    assert "Time pressure on the last 2 questions" in _text(at)
    assert at.segmented_control(key=f"cia_paper_{py}").options == ["CIA-1", "CIA-2"]
    at.segmented_control(key=f"cia_paper_{py}").set_value("CIA-2").run()
    assert not at.exception and "Not attempted" in _text(at)
    assert "Functions: 40% → 100%" in _text(at)


def test_ticking_a_silly_slip_saves_and_reclassifies(tmp_db):
    seed.ensure_seeded()
    ds, sid = _subject("MCA231"), db.get_student_by_roll("25MCA007")["id"]
    q1 = db.list_questions(ds, "CIA-1")[0]["id"]  # the demo silly loss
    at = _dashboard(subject_id=ds)
    box = at.checkbox(key=f"flag_{sid}_{q1}_0")
    assert box.value is False
    box.check().run()
    assert not at.exception
    assert db.get_silly_flags(sid, ds) == {q1}
    assert "Silly error flagged" in _text(at)
    at.checkbox(key=f"flag_{sid}_{q1}_0").uncheck().run()
    assert not at.exception and db.get_silly_flags(sid, ds) == set()


def test_flag_saved_in_db_shows_on_the_page(tmp_db):
    seed.ensure_seeded()
    ds, sid = _subject("MCA231"), db.get_student_by_roll("25MCA007")["id"]
    q3 = db.list_questions(ds, "CIA-1")[2]["id"]  # the demo concept gap
    db.set_silly_flag(sid, q3)
    at = _dashboard(subject_id=ds)
    assert not at.exception
    assert at.checkbox(key=f"flag_{sid}_{q3}_0").value is True
    assert "Silly error flagged" in _text(at)


def test_progress_needs_two_papers(tmp_db):
    seed.ensure_seeded()
    py = _subject("MCA232")
    db.save_marks(py, "CIA-2", [])  # only CIA-1 has marks now
    at = _dashboard(subject_id=py)
    assert not at.exception
    assert "Progress appears after two papers" in _text(at)


def test_new_student_sees_empty_cia_and_progress(tmp_db):
    seed.ensure_seeded()
    sid = db.add_student("25MCA096", "Empty", "MCA-A")
    db.enroll(sid, db.list_subjects()[0]["id"], 70)
    at = _dashboard(student_id=sid)
    assert not at.exception
    text = _text(at)
    assert "No CIA marks yet" in text and "No progress to show yet" in text


def _insights_page():
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["active_role"] = "Faculty"
    at.run()
    at.switch_page("views/faculty_insights.py")
    at.run()
    return at


@pytest.mark.parametrize("subject_index", [0, 1])
def test_class_insights_every_subject_and_paper(app, subject_index):
    at = _insights_page()
    assert not at.exception
    at.selectbox[0].select_index(subject_index).run()
    assert not at.exception
    for option in list(at.selectbox[1].options):
        at.selectbox[1].select(option).run()
        assert not at.exception, option
    assert "All CIAs" in at.selectbox[1].options
