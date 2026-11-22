import pytest

from core import analysis


def test_component_weights_default():
    assert analysis.component_weights(0.5) == {"CIA-1": 12.5, "CIA-2": 25.0, "CIA-3": 12.5, "ESE": 50.0}


def test_component_weights_custom():
    w = analysis.component_weights(0.6)
    assert w["CIA-1"] == pytest.approx(15) and w["CIA-2"] == pytest.approx(30)
    assert w["ESE"] == pytest.approx(40)


def test_cia_percentage():
    assert analysis.cia_percentage({"CIA-1": 20, "CIA-2": None, "CIA-3": None}) == pytest.approx(80)
    assert analysis.cia_percentage({"CIA-1": 20, "CIA-2": 30}) == pytest.approx(66.6667, abs=1e-3)
    assert analysis.cia_percentage({"CIA-1": None}) is None


def test_worked_example_on_track():
    g = analysis.goal_status(80, {"CIA-1": 20, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.5)
    assert g.status == "On track"
    assert g.earned == pytest.approx(10)
    assert g.done_weight == pytest.approx(12.5)
    assert g.remaining_weight == pytest.approx(87.5)
    assert g.current_pct == pytest.approx(80)
    assert g.required_pct == pytest.approx(80)
    assert g.final is None


def test_no_data():
    g = analysis.goal_status(80, {"CIA-1": None, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.5)
    assert g.status == "No data" and g.earned == 0 and g.current_pct is None


def test_stretch():
    g = analysis.goal_status(65, {"CIA-1": 15, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.5)
    assert g.current_pct == pytest.approx(60)
    assert g.required_pct == pytest.approx(65.7143, abs=1e-3)
    assert g.status == "Stretch"


def test_at_risk():
    g = analysis.goal_status(80, {"CIA-1": 15, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.5)
    assert g.required_pct == pytest.approx(82.857, abs=1e-2)
    assert g.status == "At risk"


def test_out_of_reach():
    g = analysis.goal_status(95, {"CIA-1": 5, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.5)
    assert g.required_pct > 100 and g.status == "Out of reach"


def test_target_already_covered_is_on_track():
    g = analysis.goal_status(5, {"CIA-1": 25, "CIA-2": 50, "CIA-3": None, "ESE": None}, 0.5)
    assert g.required_pct <= 0 and g.status == "On track"


def test_achieved_and_missed():
    full = {"CIA-1": 20, "CIA-2": 40, "CIA-3": 20, "ESE": 60}  # CIA 80/2 + 30 = 70
    g = analysis.goal_status(70, full, 0.5)
    assert g.status == "Achieved" and g.final == pytest.approx(70) and g.remaining_weight == 0
    g = analysis.goal_status(71, full, 0.5)
    assert g.status == "Missed" and g.final == pytest.approx(70)


def test_non_default_weight():
    # weight 0.6: CIA-1 20/25 -> 12 of 15 pts, 80% so far
    g = analysis.goal_status(70, {"CIA-1": 20, "CIA-2": None, "CIA-3": None, "ESE": None}, 0.6)
    assert g.earned == pytest.approx(12) and g.done_weight == pytest.approx(15)
    assert g.remaining_weight == pytest.approx(85)
    assert g.required_pct == pytest.approx((70 - 12) / 85 * 100)
    assert g.status == "On track"
    done = {"CIA-1": 25, "CIA-2": 50, "CIA-3": 25, "ESE": 50}  # 60 + 20
    assert analysis.goal_status(80, done, 0.6).final == pytest.approx(80)
