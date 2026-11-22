"""Pure grading logic (no I/O, no Streamlit)."""
from __future__ import annotations

from dataclasses import dataclass

import config

STATUSES = ("No data", "On track", "Stretch", "At risk", "Out of reach", "Achieved", "Missed")


def component_weights(cia_weight: float) -> dict[str, float]:
    """Share of the final mark (out of 100) carried by each component."""
    weights = {c: config.COMPONENTS[c] * cia_weight for c in config.CIA_COMPONENTS}
    weights["ESE"] = 100 * (1 - cia_weight)
    return weights


def cia_percentage(scores: dict[str, float | None]) -> float | None:
    """Percentage over the CIA components that have a score, or None."""
    done = {c: s for c, s in scores.items() if c in config.CIA_COMPONENTS and s is not None}
    if not done:
        return None
    return sum(done.values()) / sum(config.COMPONENTS[c] for c in done) * 100


@dataclass(frozen=True)
class GoalResult:
    status: str
    earned: float
    done_weight: float
    remaining_weight: float
    current_pct: float | None
    required_pct: float | None
    final: float | None


def goal_status(target: float, scores_by_component: dict[str, float | None],
                cia_weight: float) -> GoalResult:
    """Where a student stands against a target final mark.

    A component is done when its score is not None; components with zero
    weight are ignored.
    """
    weights = {c: w for c, w in component_weights(cia_weight).items() if w > 0}
    earned = done_weight = 0.0
    for comp, weight in weights.items():
        score = scores_by_component.get(comp)
        if score is not None:
            earned += score / config.COMPONENTS[comp] * weight
            done_weight += weight
    remaining = sum(weights.values()) - done_weight
    if remaining < 1e-9:
        remaining = 0.0
    current = earned / done_weight * 100 if done_weight else None
    required = (target - earned) / remaining * 100 if remaining else None

    if done_weight == 0:
        status, final = "No data", None
    elif remaining == 0:
        final = earned
        status = "Achieved" if earned >= target - 1e-9 else "Missed"
    else:
        final = None
        if required <= 0:
            status = "On track"
        elif required > 100:
            status = "Out of reach"
        elif required <= current:
            status = "On track"
        elif required <= current + config.STRETCH_MARGIN:
            status = "Stretch"
        else:
            status = "At risk"
    return GoalResult(status, earned, done_weight, remaining, current, required, final)
