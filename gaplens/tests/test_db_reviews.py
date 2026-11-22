import pytest

from core import db, seed


@pytest.fixture
def ds(tmp_db):
    seed.ensure_seeded()
    return [s for s in db.list_subjects() if s["code"] == "MCA231"][0]["id"]


def test_upsert_merges_fields_and_publish_toggles(ds):
    db.upsert_review(ds, "25MCA012", script_name="a.pdf", script_mime="application/pdf",
                     script=b"%PDF")
    db.upsert_review(ds, "25MCA012", final_review="Draft text")
    r = db.get_review(ds, "25MCA012")
    assert r["script_name"] == "a.pdf" and r["final_review"] == "Draft text" and not r["published"]
    assert "script" not in r and db.get_review(ds, "25MCA012", with_script=True)["script"] == b"%PDF"
    db.upsert_review(ds, "25MCA012", published=True)
    assert db.get_review(ds, "25MCA012")["published"] == 1
    db.upsert_review(ds, "25MCA012", published=False)
    assert db.get_review(ds, "25MCA012")["published"] == 0


def test_unknown_field_rejected_and_missing_is_none(ds):
    with pytest.raises(ValueError):
        db.upsert_review(ds, "25MCA012", secret="x")
    assert db.get_review(ds, "nobody") is None


def test_status_list_and_cascade(ds):
    db.upsert_review(ds, "25MCA012", script=b"x", script_name="s.png")
    status = {s["roll_no"]: s for s in db.list_review_status(ds)}
    assert status["25MCA007"] == {"roll_no": "25MCA007", "has_script": False,
                                  "has_review": True, "published": True}
    assert status["25MCA012"]["has_script"] and not status["25MCA012"]["has_review"]
    with db.transaction() as c:
        c.execute("DELETE FROM subjects WHERE id = ?", (ds,))
    assert db.list_review_status(ds) == []


def test_seeded_ese_outcomes(ds):
    from core import analysis, insights
    import config
    ese = {m["roll_no"]: m["score"] for m in db.list_ese_marks(ds)}
    assert ese["25MCA007"] == 58 and ese["25MCA012"] == 34
    assert ese["25MCA007"] >= config.ESE_PASS_MARK > ese["25MCA012"]
    r = db.get_review(ds, "25MCA007")
    assert r["published"] == 1 and "Improve" in r["final_review"]
    assert "Handwriting" in r["final_review"] or "legible" in r["final_review"].lower()
    assert db.get_review(ds, "25MCA012") is None
