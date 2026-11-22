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
