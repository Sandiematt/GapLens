"""Deterministic demo data (fixed random seeds).

Seeding is a list of steps run in order inside one transaction. A later
ticket that adds tables extends the demo by registering a step::

    from core import seed

    @seed.seed_step
    def seed_marks(conn, ctx): ...

``ctx`` is a dict the earlier steps fill (faculty id, student ids by roll,
subject ids by code) so later steps can look things up without querying.
Steps must live in a module that is imported before ``seed_all`` runs.
"""
from __future__ import annotations

import random

import config
from core import db

DS_UNITS = {
    1: ["Arrays", "Time complexity", "Recursion"],
    2: ["Linked lists", "Stacks", "Queues"],
    3: ["Binary trees", "Tree traversal", "Binary search trees"],
    4: ["Sorting", "Hashing", "Graph traversal"],
}
PY_UNITS = {
    1: ["Data types", "Control flow", "Strings"],
    2: ["Functions", "Lists and tuples", "Dictionaries and sets"],
    3: ["File handling", "Exception handling"],
    4: ["Classes and objects"],
}
SUBJECTS = [
    ("MCA231", "Data Structures", DS_UNITS),
    ("MCA232", "Python Programming", PY_UNITS),
]
DEMO_TARGETS = {"MCA231": 80, "MCA232": 75}
TARGET_SEED = 120

_STEPS: list = []


def seed_step(fn):
    """Register a seed step ``fn(conn, ctx)``. Steps run in registration order."""
    _STEPS.append(fn)
    return fn


def demo_roll(n: int) -> str:
    return f"{config.DEMO_ROLL_PREFIX}{n:03d}"


@seed_step
def seed_people_and_subjects(conn, ctx: dict) -> None:
    faculty_id = db.add_faculty(config.DEMO_FACULTY_NAME, conn=conn)
    ctx["faculty_id"] = faculty_id

    ctx["student_ids"] = {}
    for n in range(1, config.DEMO_STUDENT_COUNT + 1):
        roll = demo_roll(n)
        name = config.DEMO_STUDENT_NAME if roll == config.DEMO_STUDENT_ROLL else f"Student {n:02d}"
        ctx["student_ids"][roll] = db.add_student(roll, name, config.DEMO_CLASS, conn=conn)

    ctx["subject_ids"] = {}
    for code, name, units in SUBJECTS:
        sid = db.add_subject(faculty_id, code, name, config.DEMO_CLASS, conn=conn)
        ctx["subject_ids"][code] = sid
        for unit_no, titles in units.items():
            for title in titles:
                db.add_topic(sid, unit_no, title, conn=conn)


@seed_step
def seed_enrollments(conn, ctx: dict) -> None:
    rng = random.Random(TARGET_SEED)
    for roll, student_id in ctx["student_ids"].items():
        for code, subject_id in ctx["subject_ids"].items():
            target = rng.choice(config.TARGET_CHOICES)  # always draw: stream stays stable
            if roll == config.DEMO_STUDENT_ROLL:
                target = DEMO_TARGETS[code]
            db.enroll(student_id, subject_id, target, conn=conn)


# --- papers and marks (SAN-122) ----------------------------------------------
# (max marks, topic, difficulty) per question, in paper order.
PAPERS = {
    "MCA231": {
        "CIA-1": [(2, "Arrays", "easy"), (3, "Time complexity", "medium"),
                  (5, "Recursion", "hard"), (5, "Linked lists", "medium"),
                  (10, "Recursion", "hard")],
        "CIA-2": [(2, "Stacks", "easy"), (2, "Queues", "easy"), (3, "Linked lists", "easy"),
                  (3, "Time complexity", "medium"), (10, "Binary trees", "medium"),
                  (10, "Tree traversal", "hard"), (10, "Recursion", "medium"),
                  (10, "Stacks", "medium")],
        "CIA-3": [(5, "Sorting", "easy"), (5, "Hashing", "medium"),
                  (5, "Binary search trees", "medium"), (10, "Graph traversal", "hard")],
    },
    "MCA232": {
        "CIA-1": [(2, "Data types", "easy"), (3, "Control flow", "easy"),
                  (5, "Strings", "medium"), (5, "Functions", "medium"),
                  (10, "Lists and tuples", "hard")],
        "CIA-2": [(2, "Functions", "easy"), (3, "Dictionaries and sets", "easy"),
                  (5, "Strings", "medium"), (10, "File handling", "medium"),
                  (10, "Exception handling", "hard"), (10, "Classes and objects", "hard"),
                  (10, "Dictionaries and sets", "medium")],
    },
}
HAS_ESE = {"MCA231": True, "MCA232": False}
MARKS_SEED = {"MCA231": 1231, "MCA232": 1232}
BASE_SHARE = {"easy": 0.82, "medium": 0.62, "hard": 0.45}
BLANK_PROB = {"easy": 0.01, "medium": 0.01, "hard": 0.06}
ABILITY_SD, NOISE_SD = 0.13, 0.12
DEMO_ABILITY = {config.DEMO_STUDENT_ROLL: 0.12, "25MCA012": -0.28}
# (subject, component, 1-based question) -> score for the demo student; None = blank.
DEMO_OVERRIDES = {
    ("MCA231", "CIA-1", 1): 0.5, ("MCA231", "CIA-1", 3): 0.5, ("MCA231", "CIA-1", 5): 1.5,
    ("MCA231", "CIA-2", 7): 7,
    ("MCA232", "CIA-1", 1): 2, ("MCA232", "CIA-1", 2): 3, ("MCA232", "CIA-1", 3): 4.5,
    ("MCA232", "CIA-1", 4): 2, ("MCA232", "CIA-1", 5): 3,
    ("MCA232", "CIA-2", 5): None, ("MCA232", "CIA-2", 6): 4,
}
ESE_OVERRIDES = {("MCA231", config.DEMO_STUDENT_ROLL): 58, ("MCA231", "25MCA012"): 34}


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@seed_step
def seed_papers_and_marks(conn, ctx: dict) -> None:
    for code, papers in PAPERS.items():
        sid = ctx["subject_ids"][code]
        topic_ids = {t["title"]: t["id"] for t in db.list_topics(sid, conn=conn)}
        rng = random.Random(MARKS_SEED[code])
        rolls = list(ctx["student_ids"])
        ability = {}
        for roll in rolls:  # always draw so the stream stays stable
            a = rng.gauss(0, ABILITY_SD)
            ability[roll] = DEMO_ABILITY.get(roll, a)
        for comp, spec in papers.items():
            db.save_paper(sid, comp, [
                {"q_no": i, "max_marks": mx, "topic_id": topic_ids[topic]}
                for i, (mx, topic, _d) in enumerate(spec, start=1)], conn=conn)
            qid = {q["q_no"]: q["id"] for q in
                   conn.execute("SELECT id, q_no FROM questions WHERE subject_id = ? "
                                "AND component = ?", (sid, comp))}
            records = []
            for roll in rolls:
                for i, (mx, _topic, diff) in enumerate(spec, start=1):
                    share = _clamp(BASE_SHARE[diff] + ability[roll] + rng.gauss(0, NOISE_SD), 0, 1)
                    blank = rng.random() < BLANK_PROB[diff]
                    value = None if blank else round(share * mx * 2) / 2
                    if roll == config.DEMO_STUDENT_ROLL and (code, comp, i) in DEMO_OVERRIDES:
                        value = DEMO_OVERRIDES[(code, comp, i)]
                    records.append((qid[i], roll, None if value is None else float(value)))
            db.save_marks(sid, comp, records, conn=conn)
        if HAS_ESE[code]:
            ese = []
            for roll in rolls:
                score = _clamp(round(rng.gauss(55 + ability[roll] * 80, 12)), 10, 98)
                score = ESE_OVERRIDES.get((code, roll), score)
                ese.append((roll, float(score)))
            db.save_ese_marks(sid, ese, conn=conn)


# --- silly-error flags (SAN-124) ----------------------------------------------
# Other students flag a few attempted, below-full questions so the faculty
# flag counts have data. One question per subject draws extra flags (a
# "maybe ambiguous" question). The demo student starts with no flags so the
# tick can be shown live.
FLAG_SEED = 1240
FLAG_PROB, SUSPECT_FLAG_PROB = 0.04, 0.35
SUSPECT_QUESTIONS = {("MCA231", "CIA-2", 4), ("MCA232", "CIA-1", 3)}


@seed_step
def seed_silly_flags(conn, ctx: dict) -> None:
    rng = random.Random(FLAG_SEED)
    for code, sid in ctx["subject_ids"].items():
        rows = conn.execute(
            "SELECT q.id, q.component, q.q_no, q.max_marks, m.roll_no, m.score FROM questions q "
            "JOIN marks m ON m.question_id = q.id WHERE q.subject_id = ? "
            "ORDER BY q.component, q.q_no, m.roll_no", (sid,)).fetchall()
        for qid, comp, q_no, mx, roll, score in rows:
            p = SUSPECT_FLAG_PROB if (code, comp, q_no) in SUSPECT_QUESTIONS else FLAG_PROB
            hit = rng.random() < p  # always draw so the stream stays stable
            student_id = ctx["student_ids"].get(roll)
            if (hit and student_id is not None and roll != config.DEMO_STUDENT_ROLL
                    and score is not None and 0 < score < mx):
                db.set_silly_flag(student_id, qid, conn=conn)


def seed_all() -> dict:
    """Run every seed step in one transaction on an initialised, empty DB."""
    ctx: dict = {}
    with db.transaction() as conn:
        for step in _STEPS:
            step(conn, ctx)
    return ctx


def is_seeded() -> bool:
    return bool(db.list_faculty())


def ensure_seeded() -> bool:
    """Create the schema and seed on first run. Returns True if it seeded."""
    db.init_db()
    if is_seeded():
        return False
    seed_all()
    return True


def reset_demo() -> None:
    """Wipe everything and restore the seeded state."""
    db.reset_db()
    seed_all()
