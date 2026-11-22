"""Class insights through seeded DB: overview, heatmap matrix, topic view, flag counts."""
import pytest

from core import analysis, db, insights, seed


@pytest.fixture
def subs(tmp_db):
    seed.ensure_seeded()
    return {s["code"]: s["id"] for s in db.list_subjects()}


def test_overview_covers_all_enrolled_students(subs):
    for sid in subs.values():
        rows = insights.class_overview(sid)
        assert len(rows) == 40
        assert {"roll", "name", "target", "cia_pct", "status", "required_pct", "reasons"} <= set(rows[0])


def test_overview_flags_low_students_and_leaves_out_on_track(subs):
    rows = insights.class_overview(subs["MCA231"])
    by_roll = {r["roll"]: r for r in rows}
    assert by_roll["25MCA012"]["cia_pct"] is not None
    for r in rows:
        assert bool(r["reasons"]) == (
            (r["cia_pct"] is not None and r["cia_pct"] < 40) or r["status"] in ("At risk", "Out of reach"))
        if r["status"] == "On track" and (r["cia_pct"] or 100) >= 40:
            assert r["reasons"] == []
    assert any(r["reasons"] for r in rows)


def test_overview_reads_each_paper_once(subs, monkeypatch):
    calls = []
    real = db.list_marks
    monkeypatch.setattr(db, "list_marks", lambda *a: calls.append(a) or real(*a))
    insights.class_overview(subs["MCA232"])
    assert len(calls) == 3  # one per CIA, not per student


def test_heatmap_has_40_rows_for_each_seeded_paper(subs):
    for sid in subs.values():
        for comp in ("CIA-1", "CIA-2"):
            q, m = insights.paper_frames(sid, comp)
            matrix = analysis.class_question_matrix(q, m)
            assert len(matrix) == 40 and matrix.shape[1] == len(q)


def test_topic_view_single_paper_vs_all(subs):
    sid = subs["MCA231"]
    one = analysis.class_topic_pct([insights.paper_frames(sid, "CIA-1")])
    allp = analysis.class_topic_pct([insights.paper_frames(sid, c) for c in ("CIA-1", "CIA-2", "CIA-3")])
    assert one["pct"].is_monotonic_increasing and allp["pct"].is_monotonic_increasing
    assert len(allp) >= len(one)


def test_flag_counts_reflect_new_flag(subs):
    sid = subs["MCA232"]
    before = {r["question_id"]: r["flags"] for r in db.count_silly_flags(sid, "CIA-1")}
    student = db.get_student_by_roll("25MCA020")
    qid = next(iter(before))
    db.set_silly_flag(student["id"], qid)
    after = {r["question_id"]: r["flags"] for r in db.count_silly_flags(sid, "CIA-1")}
    assert after[qid] == before[qid] + 1
