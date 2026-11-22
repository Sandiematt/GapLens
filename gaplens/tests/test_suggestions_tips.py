"""Per-question tip templates name the topic and the scores."""
import pytest

from core import suggestions


def q(mistake, score=1.5, mx=5, topper=4.5, class_avg=2.37, topic="Recursion"):
    return {"q_no": 3, "topic": topic, "max_marks": mx, "score": None if score is None else score,
            "blank": score is None, "topper": topper, "class_avg": class_avg,
            "mistake_type": mistake}


@pytest.mark.parametrize("mistake", ["Silly error flagged", "Silly loss", "Time pressure",
                                     "Concept gap", "OK"])
def test_tip_names_topic_max_score_topper_and_class_average(mistake):
    tip = suggestions.question_tip(q(mistake))
    for part in ("Recursion", "1.5", "of 5", "topper scored 4.5", "class averaged 2.4"):
        assert part in tip, (mistake, part)


def test_not_attempted_tip_asks_for_partial_answers():
    tip = suggestions.question_tip(q("Not attempted", score=None))
    for part in ("Recursion", "5-mark", "blank", "topper scored 4.5", "class averaged 2.4",
                 "partial answer"):
        assert part in tip


def test_each_mistake_type_has_its_own_template():
    tips = {m: suggestions.question_tip(q(m, score=None if m == "Not attempted" else 1.5))
            for m in ["Not attempted", "Silly error flagged", "Silly loss", "Time pressure",
                      "Concept gap", "OK"]}
    assert len(set(tips.values())) == 6
    assert "basics" in tips["Concept gap"]
    assert "timed" in tips["Time pressure"]
    assert "slip" in tips["Silly error flagged"]
    assert "re-read" in tips["Silly loss"]


def test_ok_at_full_marks_has_no_tip():
    assert suggestions.question_tip(q("OK", score=5, topper=5)) is None


def test_ok_below_topper_says_how_far_behind():
    tip = suggestions.question_tip(q("OK", score=3.5, mx=5, topper=5, class_avg=3))
    assert "1.5 marks behind the topper" in tip
    assert "definition" in tip and "worked example" in tip and "labelled diagram" in tip


def test_ok_level_with_topper_but_short_of_full():
    tip = suggestions.question_tip(q("OK", score=4, mx=5, topper=4, class_avg=3))
    assert tip is not None and "1 mark short of full" in tip


def test_missing_topic_still_reads():
    tip = suggestions.question_tip(q("Concept gap", topic=None))
    assert "None" not in tip and "this topic" in tip


def test_title_and_potential_gain():
    assert suggestions.tip_title(q("Concept gap")) == "Q3 · Recursion · 5 marks"
    assert suggestions.potential_gain(q("Concept gap")) == 3.5
    assert suggestions.potential_gain(q("Not attempted", score=None)) == 5
