"""UI smoke tests (Streamlit AppTest) for both roles, against a temp DB."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors
from streamlit.testing.v1 import AppTest

import config
from core import db, gemini_client, seed
from ui import secrets

APP = str(Path(__file__).resolve().parents[1] / "app.py")

PAGES = {
    "Student": ["views/student_subjects.py", "views/student_dashboard.py"],
    "Faculty": ["views/faculty_subjects.py", "views/faculty_papers.py", "views/faculty_ese.py",
                "views/faculty_resources.py", "views/faculty_insights.py"],
}


def _auth(at, role="Student"):
    at.session_state["authenticated"] = True
    at.session_state["active_role"] = role
    at.session_state["auth_username"] = config.LOGIN_CREDENTIALS[role][0]
    return at


@pytest.fixture
def raw_app(tmp_db):
    seed.ensure_seeded()
    return AppTest.from_file(APP, default_timeout=30)


@pytest.fixture
def app(tmp_db):
    seed.ensure_seeded()
    return _auth(AppTest.from_file(APP, default_timeout=30), "Student")


def test_login_page_is_default_first_screen(raw_app):
    raw_app.run()
    assert not raw_app.exception
    text = " ".join(m.value for m in raw_app.markdown)
    assert "Student Login" in text
    assert "Smart marks coaching" not in text
    assert "GOAL TRACKER" not in text
    assert raw_app.segmented_control(key="login_role_tab").options == ["Student Login", "Faculty Login"]
    assert len(raw_app.sidebar.get("page_link")) == 0


def test_student_login_validation_and_role_isolation(raw_app):
    raw_app.run()
    # Wrong password rejected
    raw_app.text_input(key="login_user_Student").set_value("student")
    raw_app.text_input(key="login_pass_Student").set_value("wrong")
    raw_app.get("form_submit_button")[0].click().run()
    assert not raw_app.exception
    assert any("Invalid student username or password" in e.value for e in raw_app.error)
    assert not raw_app.session_state.get("authenticated")

    # Faculty credentials on Student Login tab are rejected with a helpful hint
    raw_app.text_input(key="login_user_Student").set_value("admin")
    raw_app.text_input(key="login_pass_Student").set_value("admin123")
    raw_app.get("form_submit_button")[0].click().run()
    assert any("Faculty Login" in e.value for e in raw_app.error)
    assert not raw_app.session_state.get("authenticated")

    # Valid Student credentials open only Student pages
    raw_app.text_input(key="login_user_Student").set_value("student")
    raw_app.text_input(key="login_pass_Student").set_value("student123")
    raw_app.get("form_submit_button")[0].click().run()
    assert not raw_app.exception
    assert raw_app.session_state["authenticated"] is True
    assert raw_app.session_state["active_role"] == "Student"
    assert len(raw_app.sidebar.get("page_link")) == len(PAGES["Student"])
    assert "Data Structures" in " ".join(m.value for m in raw_app.markdown)

    # Logout returns to Login screen
    raw_app.sidebar.button(key="logout_btn").click().run()
    assert not raw_app.exception
    assert not raw_app.session_state.get("authenticated")
    assert raw_app.segmented_control(key="login_role_tab").options == ["Student Login", "Faculty Login"]


def test_faculty_login_validation_and_role_isolation(raw_app):
    raw_app.run()
    raw_app.segmented_control(key="login_role_tab").set_value("Faculty Login").run()
    assert not raw_app.exception
    assert "Faculty Login" in " ".join(m.value for m in raw_app.markdown)

    # Student credentials on Faculty Login tab are rejected
    raw_app.text_input(key="login_user_Faculty").set_value("student")
    raw_app.text_input(key="login_pass_Faculty").set_value("student123")
    raw_app.get("form_submit_button")[0].click().run()
    assert any("Student Login" in e.value for e in raw_app.error)
    assert not raw_app.session_state.get("authenticated")

    # Valid Faculty credentials open only Faculty pages
    raw_app.text_input(key="login_user_Faculty").set_value("admin")
    raw_app.text_input(key="login_pass_Faculty").set_value("admin123")
    raw_app.get("form_submit_button")[0].click().run()
    assert not raw_app.exception
    assert raw_app.session_state["authenticated"] is True
    assert raw_app.session_state["active_role"] == "Faculty"
    assert len(raw_app.sidebar.get("page_link")) == len(PAGES["Faculty"])
    assert "Subjects you teach" in " ".join(m.value for m in raw_app.markdown)

    # Logout returns to Login screen
    raw_app.sidebar.button(key="logout_btn").click().run()
    assert not raw_app.exception
    assert not raw_app.session_state.get("authenticated")


def test_student_default_profile_and_subjects(app):
    app.run()
    assert not app.exception
    text = " ".join(m.value for m in app.markdown)
    assert "Data Structures" in text and "Python Programming" in text
    assert "Demo Student" in text and "25MCA007" in text
    assert app.number_input[0].value == 80 and app.number_input[1].value == 75


def test_page_list_covers_every_view_file():
    on_disk = {f"views/{p.name}" for p in (Path(APP).parent / "views").glob("*.py")} - {"views/__init__.py"}
    assert on_disk == {s for scripts in PAGES.values() for s in scripts}


def _open_page(role, script, **state):
    at = _auth(AppTest.from_file(APP, default_timeout=30), role)
    for key, value in state.items():
        at.session_state[key] = value
    at.run()  # switch_page is ignored before the first run
    at.switch_page(script)
    at.run()
    return at


def _every_page_case():
    """(role, script, student roll, subject code): every page for both roles with the demo
    profiles; the student dashboard (all five tabs render on each run) for both subjects
    and both demo students."""
    cases = []
    for role, scripts in PAGES.items():
        for script in scripts:
            if script == "views/student_dashboard.py":
                cases += [(role, script, roll, code) for roll in ("25MCA007", "25MCA012")
                          for code in ("MCA231", "MCA232")]
            else:
                cases.append((role, script, "25MCA007", None))
    return cases


@pytest.mark.parametrize("role,script,roll,code", _every_page_case())
def test_every_page_renders(app, role, script, roll, code):
    state = {"student_id": db.get_student_by_roll(roll)["id"]}
    if code:
        state["selected_subject_id"] = next(s["id"] for s in db.list_subjects() if s["code"] == code)
    at = _open_page(role, script, **state)
    assert not at.exception, (role, script, roll, code)
    assert len(at.sidebar.get("page_link")) == len(PAGES[role])
    if script == "views/student_dashboard.py":
        labels = [t.label for t in at.tabs]
        assert {"Goal", "CIA Analysis", "Weak Topics & Resources", "Progress", "ESE"} <= set(labels)


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
    _auth(app, "Faculty")
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
    _auth(app, "Faculty")
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
    student = _auth(AppTest.from_file(APP, default_timeout=30), "Student")
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
    at = _auth(AppTest.from_file(APP, default_timeout=30), "Student")
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
    at = _auth(AppTest.from_file(APP, default_timeout=30), "Faculty")
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


# --- ESE tab and ESE Scripts page (SAN-127) ---------------------------------------
def _ese_text(at):
    return _text(at) + " ".join(i.value for i in at.info)


def test_ese_tab_pass_with_published_review(tmp_db):
    seed.ensure_seeded()
    at = _dashboard(subject_id=_subject("MCA231"))
    assert not at.exception
    text = _text(at)
    assert ">Pass<" in text and "58 / 100" in text and "Presentation feedback" in text
    assert "Doing well" in text and "Improve" in text
    assert "Focus for supplementary exam" not in text


def test_ese_tab_fail_shows_supplementary_focus(tmp_db):
    seed.ensure_seeded()
    at = _dashboard(student_id=db.get_student_by_roll("25MCA012")["id"],
                    subject_id=_subject("MCA231"))
    assert not at.exception
    text = _text(at)
    assert ">Fail<" in text and "34 / 100" in text
    assert "Focus for supplementary exam" in text
    assert "published a review yet" in text


def test_ese_tab_without_ese_marks(tmp_db):
    seed.ensure_seeded()
    at = _dashboard(subject_id=_subject("MCA232"))
    assert not at.exception
    assert any("ESE mark has not been entered" in i.value for i in at.info)


def _ese_page():
    at = _auth(AppTest.from_file(APP, default_timeout=30), "Faculty")
    at.run()
    at.switch_page("views/faculty_ese.py")
    at.run()
    return at


def _pick_roll(at, roll):
    next(s for s in at.selectbox if s.label == "Student").select(roll).run()


def test_faculty_checklist_to_publish_to_unpublish(tmp_db):
    seed.ensure_seeded()
    ds, roll = _subject("MCA231"), "25MCA012"
    at = _ese_page()
    assert not at.exception and at.button[[b.label for b in at.button].index("Generate AI review")].disabled
    _pick_roll(at, roll)
    assert not at.exception
    assert at.text_area[0].value == ""  # 25MCA007's published review must not leak here
    ident = f"0_{ds}_{roll}"
    at.checkbox(key=f"ese_chk_headings_{ident}").check().run()
    at.button(key=f"ese_gen_{ident}").click().run()
    assert not at.exception
    r = db.get_review(ds, roll)
    assert not r["published"] and "Doing well" in r["final_review"]
    assert at.text_area[0].value == r["final_review"]
    assert [m for m in at.markdown if "Draft" in m.value]
    # a student cannot see the draft
    stu = _dashboard(student_id=db.get_student_by_roll(roll)["id"], subject_id=ds)
    assert "published a review yet" in _text(stu) and "Doing well" not in _text(stu)
    at.text_area[0].set_value("Edited review. Improve spacing.")
    at.button(key=f"ese_publish_{ident}").click().run()
    assert db.get_review(ds, roll)["published"] == 1
    stu = _dashboard(student_id=db.get_student_by_roll(roll)["id"], subject_id=ds)
    assert "Edited review" in _text(stu)
    at.button(key=f"ese_unpublish_{ident}").click().run()
    assert not at.exception and db.get_review(ds, roll)["published"] == 0
    stu = _dashboard(student_id=db.get_student_by_roll(roll)["id"], subject_id=ds)
    assert "Edited review" not in _text(stu) and "published a review yet" in _text(stu)


def test_switching_student_never_shows_previous_draft(tmp_db):
    seed.ensure_seeded()
    at = _ese_page()
    _pick_roll(at, "25MCA007")
    assert "Doing well" in at.text_area[0].value
    _pick_roll(at, "25MCA012")
    assert at.text_area[0].value == ""
    _pick_roll(at, "25MCA007")
    assert "Doing well" in at.text_area[0].value


# --- Gemini course plan and AI review (SAN-128); never touches the network -----------
CANNED_PLAN = {"subject_code": "mca233", "subject_name": "Design and Analysis of Algorithms",
               "units": [{"unit_no": 1, "title": "Basics", "topics": ["Asymptotic notation", "Recurrences"]},
                         {"unit_no": 2, "title": "Divide and conquer", "topics": ["Merge sort", " "]}]}
CANNED_REVIEW = {"strengths": ["Clear headings"],
                 "improvements": [{"area": "Margins", "observation": "Cramped.", "tip": "Leave space."}],
                 "summary": "Tidy overall."}


def _fake_gemini(monkeypatch, reply):
    """A key plus a stub SDK client; returns the list of generate_content calls."""
    calls = []

    def generate_content(*, model, contents, config):
        calls.append(model)
        if isinstance(reply, BaseException):
            raise reply
        return SimpleNamespace(text=json.dumps(reply))

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content, list=lambda: []))
    monkeypatch.setattr(secrets, "get_gemini_key", lambda: "test-key")
    monkeypatch.setattr(gemini_client, "client_factory", lambda key: client)
    return calls


def _button(at, label):
    return next(b for b in at.button if b.label == label)


def test_without_key_gemini_buttons_are_disabled_with_messages(app):
    _faculty_app(app)
    assert _button(app, "Parse with Gemini").disabled
    app.file_uploader[0].upload("plan.pdf", b"%PDF-1.4", "application/pdf").run()
    assert _button(app, "Parse with Gemini").disabled
    assert any("Manually" in i.value and "secrets.toml" in i.value for i in app.info)
    at = _ese_page()
    _pick_roll(at, "25MCA007")
    assert not at.exception and _button(at, "Generate AI review").disabled
    assert any("No Gemini API key" in c.value for c in at.caption)


def test_course_plan_flow_creates_subject_and_topics(app, monkeypatch):
    calls = _fake_gemini(monkeypatch, CANNED_PLAN)
    _faculty_app(app)
    assert _button(app, "Parse with Gemini").disabled  # no file yet
    app.file_uploader[0].upload("DAA_plan.pdf", b"%PDF-1.4 plan", "application/pdf").run()
    assert not app.exception and calls == []  # nothing is sent before the click
    app.button(key="plan_parse").click().run()
    assert not app.exception and len(calls) == 1
    assert "DAA_plan.pdf" in _text(app) and "2 units found" in _text(app)
    assert [t.value for t in app.text_input[:3]] == ["MCA233", "Design and Analysis of Algorithms", "MCA-A"]
    table = app.dataframe[0].value
    assert list(table["topic"]) == ["Asymptotic notation", "Recurrences", "Merge sort"]
    app.get("form_submit_button")[0].click().run()
    assert not app.exception and not app.error
    subj = [s for s in db.list_subjects() if s["code"] == "MCA233"][0]
    assert subj["cia_weight"] == 0.5
    assert [(t["unit_no"], t["title"]) for t in db.list_topics(subj["id"])] == [
        (1, "Asymptotic notation"), (1, "Recurrences"), (2, "Merge sort")]
    assert "course_plan_parsed" not in app.session_state
    assert any("Created MCA233" in s.value for s in app.success)
    assert len(calls) == 1  # creating the subject made no further API call


def test_course_plan_error_is_shown_and_manual_tab_still_works(app, monkeypatch):
    quota = genai_errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}})
    _fake_gemini(monkeypatch, quota)
    _faculty_app(app)
    app.file_uploader[0].upload("plan.png", b"\x89PNG", "image/png").run()
    app.button(key="plan_parse").click().run()
    assert not app.exception and any("quota" in e.value for e in app.error)
    app.text_input[0].set_value("MCA250")
    app.text_input[1].set_value("Manual")
    app.text_area[0].set_value("1 | One")
    app.get("form_submit_button")[0].click().run()
    assert not app.exception and any(s["code"] == "MCA250" for s in db.list_subjects())


def test_ai_review_writes_a_draft_students_cannot_see(tmp_db, monkeypatch):
    seed.ensure_seeded()
    calls = _fake_gemini(monkeypatch, CANNED_REVIEW)
    ds, roll = _subject("MCA231"), "25MCA012"
    at = _ese_page()
    _pick_roll(at, roll)
    assert _button(at, "Generate AI review").disabled  # no script stored yet
    db.upsert_review(ds, roll, script_name="script.png", script_mime="image/png", script=b"\x89PNG")
    at.run()
    assert not _button(at, "Generate AI review").disabled and calls == []
    at.button(key=f"ese_ai_0_{ds}_{roll}").click().run()
    assert not at.exception and len(calls) == 1
    r = db.get_review(ds, roll)
    assert r["ai_review"] == r["final_review"] and not r["published"]
    assert "Clear headings" in r["final_review"] and "**Improve**" in r["final_review"]
    assert at.text_area[0].value == r["final_review"]
    stu = _dashboard(student_id=db.get_student_by_roll(roll)["id"], subject_id=ds)
    assert "Clear headings" not in _text(stu) and "published a review yet" in _text(stu)
    at.button(key=f"ese_publish_0_{ds}_{roll}").click().run()
    stu = _dashboard(student_id=db.get_student_by_roll(roll)["id"], subject_id=ds)
    assert "Clear headings" in _text(stu)


def test_ai_review_error_and_large_script_warning(tmp_db, monkeypatch):
    seed.ensure_seeded()
    _fake_gemini(monkeypatch, TimeoutError("timed out"))
    monkeypatch.setattr(config, "GEMINI_SCRIPT_WARN_MB", 0)
    ds, roll = _subject("MCA231"), "25MCA012"
    db.upsert_review(ds, roll, script_name="script.pdf", script_mime="application/pdf", script=b"%PDF")
    at = _ese_page()
    _pick_roll(at, roll)
    assert any("may reject files this large" in w.value for w in at.warning)
    at.button(key=f"ese_ai_0_{ds}_{roll}").click().run()
    assert not at.exception
    assert any("manual checklist instead" in e.value for e in at.error)
    assert not (db.get_review(ds, roll)["final_review"] or "")


# --- polish pass: privacy and ESE-fail status ------------------------------------------
def test_student_picker_shows_roll_numbers_only(app):
    app.run()
    assert not app.exception
    picker = app.sidebar.selectbox(key="profile_widget_Student")
    assert "25MCA007 · MCA-A" in picker.options
    names = {s["name"] for s in db.list_students()}
    assert not any(name in option for option in picker.options for name in names)
    assert "Demo Student" in _text(app)  # the signed-in student's own chip still shows the name


def test_faculty_picker_still_shows_names(app):
    _faculty_app(app)
    assert config.DEMO_FACULTY_NAME in app.sidebar.selectbox(key="profile_widget_Faculty").options


def test_ese_fail_shows_missed_on_goal_and_ese_tabs(tmp_db):
    seed.ensure_seeded()
    ds = _subject("MCA231")
    sid = db.get_student_by_roll("25MCA012")["id"]
    db.set_target(sid, ds, 40)  # a target the final mark clears, but the ESE is a fail
    at = _dashboard(student_id=sid, subject_id=ds)
    assert not at.exception
    text = _text(at)
    assert "/100: Missed" in text and "/100: Achieved" not in text  # the goal hero
    assert "below the pass mark" in text


def test_sidebar_role_switch_requires_faculty_credentials_and_allows_roundtrip(app):
    app.run()
    assert not app.exception
    assert app.session_state["active_role"] == "Student"

    # Clicking Faculty opens the dedicated Faculty Login screen without escalating role yet
    app.sidebar.segmented_control(key="role_switch_widget").set_value("Faculty").run()
    assert not app.exception
    assert app.session_state["active_role"] == "Student"
    assert app.session_state.get("confirm_faculty_switch") is True
    assert "Faculty Login" in _text(app)
    assert len(app.sidebar.get("page_link")) == 0

    # Student credentials and wrong credentials are rejected on the Faculty Login screen
    app.text_input(key="switch_faculty_user").set_value("student")
    app.text_input(key="switch_faculty_pass").set_value("student123")
    app.get("form_submit_button")[0].click().run()
    assert any("Student Login" in e.value for e in app.error)
    assert app.session_state["active_role"] == "Student"

    app.text_input(key="switch_faculty_user").set_value("admin")
    app.text_input(key="switch_faculty_pass").set_value("wrong")
    app.get("form_submit_button")[0].click().run()
    assert any("Invalid faculty username or password" in e.value for e in app.error)
    assert app.session_state["active_role"] == "Student"

    # Back to Student Portal returns to Student view cleanly
    app.button(key="switch_faculty_cancel").click().run()
    assert not app.exception
    assert not app.session_state.get("confirm_faculty_switch")
    assert app.session_state["active_role"] == "Student"
    assert len(app.sidebar.get("page_link")) == len(PAGES["Student"])

    # Re-open Faculty Login and verify with valid Faculty credentials -> opens Faculty portal
    app.sidebar.segmented_control(key="role_switch_widget").set_value("Faculty").run()
    app.text_input(key="switch_faculty_user").set_value("admin")
    app.text_input(key="switch_faculty_pass").set_value("admin123")
    app.get("form_submit_button")[0].click().run()
    assert not app.exception
    assert app.session_state["active_role"] == "Faculty"
    assert app.session_state["auth_username"] == "admin"
    assert "switch_faculty_pass" not in app.session_state
    assert len(app.sidebar.get("page_link")) == len(PAGES["Faculty"])
    assert "Subjects you teach" in _text(app)

    # Switching from Faculty -> Student works in one click and re-enables Faculty login gate
    app.sidebar.segmented_control(key="role_switch_widget").set_value("Student").run()
    assert not app.exception
    assert app.session_state["active_role"] == "Student"
    assert app.session_state["auth_username"] == "student"
    assert len(app.sidebar.get("page_link")) == len(PAGES["Student"])

    app.sidebar.segmented_control(key="role_switch_widget").set_value("Faculty").run()
    assert app.session_state["active_role"] == "Student"
    assert app.session_state.get("confirm_faculty_switch") is True
    assert "Faculty Login" in _text(app)
