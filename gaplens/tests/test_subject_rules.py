import pytest

from core import db, subject_rules as rules


def test_parse_unit_prefixed_lines():
    text = "1 | Arrays\n2 | Stacks\nUnit 2 | Queues"
    assert rules.parse_topic_lines(text) == [(1, "Arrays"), (2, "Stacks"), (2, "Queues")]


def test_lines_without_prefix_follow_previous_unit_and_blanks_are_skipped():
    text = "Intro\n\n  3 | Trees  \nGraphs\n"
    assert rules.parse_topic_lines(text) == [(1, "Intro"), (3, "Trees"), (3, "Graphs")]


def test_non_numeric_prefix_is_part_of_the_title():
    assert rules.parse_topic_lines("a | b") == [(1, "a | b")]


def test_subject_validation_reports_every_empty_field():
    errs = rules.validate_subject("", " ", "", 50, [])
    assert len(errs) == 4
    assert rules.validate_subject("MCA1", "N", "MCA-A", 50, [(1, "x")]) == []


def test_subject_validation_rejects_bad_weight_and_duplicate_topics():
    assert rules.validate_subject("A", "B", "C", 120, [(1, "x")])
    assert rules.validate_subject("A", "B", "C", 50, [(1, "Stacks"), (2, "stacks")])


def test_topic_row_validation():
    assert rules.validate_topic_rows([{"unit_no": 1, "title": "A"}]) == []
    assert rules.validate_topic_rows([{"unit_no": 1, "title": " "}])
    assert rules.validate_topic_rows([{"unit_no": 0, "title": "A"}])
    assert rules.validate_topic_rows([{"unit_no": None, "title": "A"}])
    assert rules.validate_topic_rows([{"unit_no": 1, "title": "A"}, {"unit_no": 2, "title": "a"}])


# --- storage ---------------------------------------------------------------
@pytest.fixture
def subj(tmp_db):
    db.init_db()
    fid = db.add_faculty("F")
    return fid, db.create_subject_with_topics(fid, "x1", "Sub", "MCA-A", 0.4, [(1, "A"), (2, "B")])


def test_create_subject_with_topics_is_atomic_and_unique(subj, tmp_db):
    fid, sid = subj
    assert [t["title"] for t in db.list_topics(sid)] == ["A", "B"]
    assert db.list_subjects()[0]["code"] == "X1" and db.list_subjects()[0]["cia_weight"] == 0.4
    with pytest.raises(db.DuplicateError):
        db.create_subject_with_topics(fid, "X1", "Other", "MCA-A", 0.5, [(1, "Z")])
    assert len(db.list_subjects()) == 1


def test_update_topics_adds_renames_removes(subj):
    _, sid = subj
    a, b = db.list_topics(sid)
    db.update_topics(sid, [{"id": a["id"], "unit_no": 1, "title": "A renamed"},
                           {"id": None, "unit_no": 3, "title": "C"}])
    topics = db.list_topics(sid)
    assert [(t["unit_no"], t["title"]) for t in topics] == [(1, "A renamed"), (3, "C")]
    assert topics[0]["id"] == a["id"]


def test_update_topics_ignores_ids_of_other_subjects(subj):
    fid, sid = subj
    other = db.create_subject_with_topics(fid, "Y", "Y", "MCA-A", 0.5, [(1, "Keep")])
    foreign = db.list_topics(other)[0]
    db.update_topics(sid, [{"id": foreign["id"], "unit_no": 1, "title": "Hijack"}])
    assert [t["title"] for t in db.list_topics(other)] == ["Keep"]


def test_removing_a_topic_untags_questions_instead_of_failing(subj):
    """Simulates SAN-122's questions table (topic_id ON DELETE SET NULL)."""
    _, sid = subj
    a, b = db.list_topics(sid)
    with db.transaction() as c:
        c.execute("CREATE TABLE questions (id INTEGER PRIMARY KEY, "
                  "topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL)")
        c.execute("INSERT INTO questions (topic_id) VALUES (?)", (a["id"],))
    db.update_topics(sid, [{"id": b["id"], "unit_no": 2, "title": "B"}])
    with db.transaction() as c:
        assert c.execute("SELECT topic_id FROM questions").fetchone()[0] is None


def test_subject_summaries_count_students_and_topics_for_owner_only(subj):
    fid, sid = subj
    other_f = db.add_faculty("G")
    db.create_subject_with_topics(other_f, "Z", "Z", "MCA-A", 0.5, [(1, "t")])
    s = db.add_student("R1", "S", "MCA-A")
    db.enroll(s, sid)
    rows = db.list_subject_summaries(fid)
    assert [(r["code"], r["student_count"], r["topic_count"]) for r in rows] == [("X1", 1, 2)]
