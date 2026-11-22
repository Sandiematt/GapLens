"""Pure grading logic (no I/O, no Streamlit)."""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

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


# --- per-paper CIA analysis (SAN-124) -----------------------------------------
NOT_ATTEMPTED, SILLY_FLAGGED, SILLY_LOSS = "Not attempted", "Silly error flagged", "Silly loss"
TIME_PRESSURE, CONCEPT_GAP, OK = "Time pressure", "Concept gap", "OK"
MISTAKE_TYPES = (NOT_ATTEMPTED, SILLY_FLAGGED, SILLY_LOSS, TIME_PRESSURE, CONCEPT_GAP, OK)

TABLE_COLUMNS = ["question_id", "q_no", "topic_id", "topic", "max_marks", "score", "blank",
                 "topper", "class_avg", "percentile", "mistake_type", "flagged"]


@dataclass(frozen=True)
class PaperAnalysis:
    table: pd.DataFrame
    total: float
    max_total: float
    topper_total: float
    class_avg_total: float
    percentile: float
    class_size: int
    time_pressure: bool
    student_drop: float | None
    class_drop: float | None


def percentile_of(value: float, values) -> float:
    """(number below + 0.5 x number tied) / n x 100. ``values`` includes ``value``."""
    values = list(values)
    below = sum(v < value - 1e-9 for v in values)
    ties = sum(abs(v - value) <= 1e-9 for v in values)
    return (below + 0.5 * ties) / len(values) * 100


_EPS = 1e-9


def _pct(scores, maxes) -> float:
    return float(sum(scores)) / float(sum(maxes)) * 100


def time_pressure_drops(student_scores, class_avg_scores, maxes):
    """(student drop, class drop) in % points from the first n-k to the last k
    questions, k = ceil(n/3); (None, None) with fewer than the minimum questions."""
    n = len(maxes)
    if n < config.TIME_PRESSURE_MIN_QUESTIONS:
        return None, None
    k = math.ceil(n / 3)
    drop = lambda s: _pct(s[: n - k], maxes[: n - k]) - _pct(s[n - k:], maxes[n - k:])  # noqa: E731
    return drop(list(student_scores)), drop(list(class_avg_scores))


def classify_question(*, blank: bool, flagged: bool, share: float, class_avg_share: float,
                      class_strong_fraction: float, paper_time_pressure: bool,
                      in_last_third: bool) -> str:
    """Mistake type of one question, checked in the spec's order."""
    if blank:
        return NOT_ATTEMPTED
    if flagged:
        return SILLY_FLAGGED
    if (class_strong_fraction >= config.SILLY_CLASS_FRACTION - _EPS
            and share < config.SILLY_STUDENT_SHARE - _EPS):
        return SILLY_LOSS
    if paper_time_pressure and in_last_third and share < class_avg_share - _EPS:
        return TIME_PRESSURE
    if share <= class_avg_share - config.GAP_POINTS / 100 + _EPS:
        return CONCEPT_GAP
    return OK


def analyse_paper(questions_df: pd.DataFrame, marks_df: pd.DataFrame, roll_no: str,
                  flagged_question_ids) -> PaperAnalysis | None:
    """Question-by-question analysis of one roll on one paper, or None if it has no marks.

    ``questions_df``: question_id, q_no, topic_id, topic, max_marks.
    ``marks_df``: question_id, roll_no, score (NaN/None = not attempted).
    The class is every roll on the paper; blanks count as 0 in class figures.
    """
    if questions_df.empty or marks_df.empty or roll_no not in set(marks_df["roll_no"]):
        return None
    qs = questions_df.sort_values("q_no").reset_index(drop=True)
    qids = list(qs["question_id"])
    raw = (marks_df.pivot_table(index="roll_no", columns="question_id", values="score",
                                aggfunc="first", dropna=False)
           .reindex(columns=qids).astype(float))
    class_scores = raw.fillna(0.0)  # blanks count as 0 for the class
    mine_raw = raw.loc[roll_no]
    mine = class_scores.loc[roll_no]
    totals = class_scores.sum(axis=1)
    topper_roll = totals.sort_index().idxmax()
    flagged = set(flagged_question_ids or ())
    maxes = qs["max_marks"].astype(float).to_numpy()

    table = qs[["question_id", "q_no", "topic_id", "topic", "max_marks"]].copy()
    table["max_marks"] = maxes
    table["score"] = mine_raw.to_numpy()
    table["blank"] = mine_raw.isna().to_numpy()
    table["topper"] = class_scores.loc[topper_roll].to_numpy()
    table["class_avg"] = class_scores.mean(axis=0).to_numpy()
    table["percentile"] = [percentile_of(mine[q], class_scores[q]) for q in qids]
    table["flagged"] = [q in flagged for q in qids]

    student_drop, class_drop = time_pressure_drops(mine.to_numpy(), table["class_avg"].to_numpy(),
                                                   maxes)
    time_pressure = (student_drop is not None
                     and student_drop >= config.TIME_PRESSURE_DROP - _EPS
                     and student_drop - class_drop >= config.TIME_PRESSURE_EXCESS - _EPS)
    n = len(qids)
    first_last = n - math.ceil(n / 3)
    shares = class_scores / maxes  # per roll, per question
    strong = (shares >= config.SILLY_CLASS_SHARE - _EPS).mean(axis=0).to_numpy()
    table["mistake_type"] = [
        classify_question(blank=bool(table["blank"].iat[i]), flagged=bool(table["flagged"].iat[i]),
                          share=mine.iat[i] / maxes[i],
                          class_avg_share=table["class_avg"].iat[i] / maxes[i],
                          class_strong_fraction=strong[i], paper_time_pressure=time_pressure,
                          in_last_third=i >= first_last)
        for i in range(n)]
    return PaperAnalysis(
        table=table[TABLE_COLUMNS], total=float(mine.sum()), max_total=float(maxes.sum()),
        topper_total=float(totals.max()), class_avg_total=float(totals.mean()),
        percentile=percentile_of(totals[roll_no], totals), class_size=int(len(totals)),
        time_pressure=bool(time_pressure), student_drop=student_drop, class_drop=class_drop)


def _tagged(table: pd.DataFrame) -> pd.DataFrame:
    """Questions that have a topic, with blank scores as 0 and int topic ids."""
    t = table[table["topic_id"].notna()].copy()
    t["topic_id"] = t["topic_id"].astype(int)
    t["score"] = t["score"].fillna(0.0)
    return t


def topic_progress(analyses: dict[str, PaperAnalysis]) -> pd.DataFrame:
    """Long-form topic % per paper: component, topic_id, topic, pct.

    pct = sum of scores / sum of max x 100 (blanks are 0). Components follow
    config order; untagged questions are left out.
    """
    frames = []
    for comp in [c for c in config.CIA_COMPONENTS if c in analyses]:
        t = _tagged(analyses[comp].table)
        if t.empty:
            continue
        g = (t.groupby("topic_id", sort=False)
             .agg(topic=("topic", "first"), score=("score", "sum"), mx=("max_marks", "sum"))
             .reset_index())
        g["pct"] = g["score"] / g["mx"] * 100
        g.insert(0, "component", comp)
        frames.append(g[["component", "topic_id", "topic", "pct"]])
    if not frames:
        return pd.DataFrame(columns=["component", "topic_id", "topic", "pct"])
    return pd.concat(frames, ignore_index=True)


def topic_losses(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """Topics ranked by marks lost across papers: topic_id, topic, lost, max, lost_pct.

    Flagged (silly-error) questions are left out; blanks lose the full marks.
    Grouped by topic id; untagged questions are left out. Most marks lost first.
    """
    cols = ["topic_id", "topic", "lost", "max", "lost_pct"]
    frames = [t[~t["flagged"].astype(bool)] for t in tables if not t.empty]
    if not frames:
        return pd.DataFrame(columns=cols)
    t = _tagged(pd.concat(frames, ignore_index=True))
    if t.empty:
        return pd.DataFrame(columns=cols)
    t["lost"] = t["max_marks"] - t["score"]
    g = (t.groupby("topic_id", sort=False)
         .agg(topic=("topic", "first"), lost=("lost", "sum"), max=("max_marks", "sum"))
         .reset_index())
    g["lost_pct"] = g["lost"] / g["max"] * 100
    g = g.sort_values(["lost", "lost_pct", "topic"], ascending=[False, False, True], kind="stable")
    return g[cols].reset_index(drop=True)


# --- class-level views (SAN-126) ---------------------------------------------------
def class_question_matrix(questions_df: pd.DataFrame, marks_df: pd.DataFrame) -> pd.DataFrame:
    """Roll numbers x "Q<n>" columns holding % of each question's max (blanks are 0)."""
    qs = questions_df.sort_values("q_no")
    cols = [f"Q{int(n)}" for n in qs["q_no"]]
    if marks_df.empty or qs.empty:
        return pd.DataFrame(columns=cols, dtype=float)
    wide = (marks_df.pivot_table(index="roll_no", columns="question_id", values="score",
                                 aggfunc="first", dropna=False)
            .reindex(columns=list(qs["question_id"])).fillna(0.0))
    pct = wide.div(qs["max_marks"].to_numpy(), axis=1) * 100
    pct.columns = cols
    pct.index.name = None
    return pct.sort_index()


def class_topic_pct(papers: list[tuple[pd.DataFrame, pd.DataFrame]]) -> pd.DataFrame:
    """Class % per topic across the papers given: topic, pct, worst first.

    pct = sum of all scores / sum of all max (blanks are 0); untagged questions are ignored.
    """
    parts = []
    for questions, marks in papers:
        if questions.empty or marks.empty:
            continue
        n_rolls = marks["roll_no"].nunique()
        tagged = questions[questions["topic_id"].notna()]
        scored = marks.merge(tagged[["question_id", "topic_id", "topic"]], on="question_id")
        got = scored.groupby("topic_id")["score"].sum()
        mx = tagged.groupby("topic_id")["max_marks"].sum() * n_rolls
        names = tagged.groupby("topic_id")["topic"].first()
        parts.append(pd.DataFrame({"topic": names, "score": got, "mx": mx}).fillna({"score": 0.0}))
    if not parts:
        return pd.DataFrame(columns=["topic", "pct"])
    g = pd.concat(parts).groupby(level=0).agg(topic=("topic", "first"), score=("score", "sum"),
                                              mx=("mx", "sum"))
    g["pct"] = g["score"] / g["mx"] * 100
    return (g[["topic", "pct"]].sort_values(["pct", "topic"], kind="stable").reset_index(drop=True))


def early_warning_reasons(cia_pct: float | None, goal: GoalResult) -> list[str]:
    """Why a student is flagged; an empty list means not flagged."""
    reasons = []
    if cia_pct is not None and cia_pct < config.EARLY_WARNING_CIA_PCT:
        reasons.append(f"CIA average below {config.EARLY_WARNING_CIA_PCT}%")
    if goal.status in ("At risk", "Out of reach"):
        reasons.append(f"{goal.status} target")
    return reasons
