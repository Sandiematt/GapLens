from core import suggestions as s

KEYS = [k for k, _l, _t in s.PRESENTATION_CHECKLIST]


def test_checklist_has_eight_items_with_tips():
    assert len(KEYS) == 8 and len(set(KEYS)) == 8
    assert all(label and len(tip) > 30 for _k, label, tip in s.PRESENTATION_CHECKLIST)


def test_one_tip_per_no_and_yes_listed_as_strength():
    answers = {k: True for k in KEYS}
    answers[KEYS[0]] = False
    answers[KEYS[2]] = False
    md = s.checklist_review(answers)
    doing, improve = md.split("**Improve**")
    assert "**Doing well**" in doing
    labels = {k: l for k, l, _t in s.PRESENTATION_CHECKLIST}
    tips = {k: t for k, _l, t in s.PRESENTATION_CHECKLIST}
    for k in KEYS:
        if answers[k]:
            assert labels[k] in doing and tips[k] not in md
        else:
            assert tips[k] in improve and labels[k] not in doing
    assert improve.count("\n- ") == 2


def test_all_yes_and_all_no():
    yes = s.checklist_review({k: True for k in KEYS})
    assert "Improve" in yes and yes.count("\n- ") == 8 + 1 or "Nothing" in yes
    assert all(t not in yes for _k, _l, t in s.PRESENTATION_CHECKLIST)
    no = s.checklist_review({k: False for k in KEYS})
    assert all(t in no for _k, _l, t in s.PRESENTATION_CHECKLIST)
    assert "Doing well" in no


def test_split_review_round_trip_and_free_text():
    md = s.checklist_review({k: k != KEYS[0] for k in KEYS})
    good, improve = s.split_review(md)
    assert s.PRESENTATION_CHECKLIST[1][1] in good
    assert s.PRESENTATION_CHECKLIST[0][2] in improve and "Doing well" not in good
    assert s.split_review("Just write neatly.") == ("", "Just write neatly.")
