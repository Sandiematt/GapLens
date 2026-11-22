"""SQLite storage layer. Plain functions, no Streamlit import.

Every call opens a fresh connection (foreign keys ON) unless an open
``conn`` is passed in, which lets callers such as the seed batch many
writes into one transaction.

Adding tables in a later ticket: append a ``CREATE TABLE IF NOT EXISTS``
statement with ``register_table(...)`` below (or add it to ``_SCHEMA``).
``init_db`` runs every statement; ``reset_db`` drops every table and
re-runs them, so new tables are picked up automatically.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import config

# Tests monkeypatch this attribute to point at a temporary file.
DB_PATH: Path = config.DB_PATH


class DuplicateError(ValueError):
    """Raised when a unique value (e.g. a roll number) already exists."""


# --- schema -----------------------------------------------------------------
_SCHEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        class_name TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        cia_weight REAL NOT NULL DEFAULT 0.5,
        UNIQUE (code, class_name)
    )""",
    """CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        unit_no INTEGER NOT NULL DEFAULT 1,
        title TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        component TEXT NOT NULL,
        q_no INTEGER NOT NULL,
        max_marks REAL NOT NULL,
        topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
        UNIQUE (subject_id, component, q_no)
    )""",
    """CREATE TABLE IF NOT EXISTS marks (
        question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        roll_no TEXT NOT NULL,
        score REAL,
        PRIMARY KEY (question_id, roll_no)
    )""",
    """CREATE TABLE IF NOT EXISTS ese_marks (
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        roll_no TEXT NOT NULL,
        score REAL NOT NULL,
        PRIMARY KEY (subject_id, roll_no)
    )""",
    """CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        target REAL,
        UNIQUE (student_id, subject_id)
    )""",
]


def register_table(create_sql: str) -> None:
    """Add a CREATE TABLE statement to the schema (idempotent)."""
    if create_sql not in _SCHEMA:
        _SCHEMA.append(create_sql)


# --- connections ------------------------------------------------------------
def connect() -> sqlite3.Connection:
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def _session(conn: sqlite3.Connection | None = None):
    """Yield ``conn`` untouched, or a fresh connection committed on exit."""
    if conn is not None:
        yield conn
        return
    own = connect()
    try:
        yield own
        own.commit()
    except Exception:
        own.rollback()
        raise
    finally:
        own.close()


@contextmanager
def transaction():
    """One connection for a batch of writes; commits at the end."""
    with _session() as conn:
        yield conn


def _rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


# --- schema lifecycle -------------------------------------------------------
def init_db() -> None:
    with _session() as conn:
        for stmt in _SCHEMA:
            conn.execute(stmt)


def reset_db() -> None:
    """Drop every table, then recreate the empty schema."""
    conn = connect()
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'")]
        for name in names:
            conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        conn.commit()
    finally:
        conn.close()
    init_db()


# --- faculty ----------------------------------------------------------------
def add_faculty(name: str, conn=None) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Name is required.")
    with _session(conn) as c:
        try:
            return c.execute("INSERT INTO faculty (name) VALUES (?)", (name,)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateError(f"A faculty profile named {name} already exists.") from exc


def list_faculty() -> list[dict]:
    with _session() as c:
        return _rows(c.execute("SELECT * FROM faculty ORDER BY id"))


def get_faculty(faculty_id: int) -> dict | None:
    with _session() as c:
        r = c.execute("SELECT * FROM faculty WHERE id = ?", (faculty_id,)).fetchone()
        return dict(r) if r else None


# --- students ---------------------------------------------------------------
def add_student(roll_no: str, name: str, class_name: str, conn=None) -> int:
    roll_no, name, class_name = roll_no.strip().upper(), name.strip(), class_name.strip()
    if not (roll_no and name and class_name):
        raise ValueError("Roll number, name and class are all required.")
    with _session(conn) as c:
        try:
            return c.execute(
                "INSERT INTO students (roll_no, name, class_name) VALUES (?, ?, ?)",
                (roll_no, name, class_name)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateError(f"Roll number {roll_no} already exists.") from exc


def list_students(class_name: str | None = None) -> list[dict]:
    with _session() as c:
        if class_name:
            cur = c.execute("SELECT * FROM students WHERE class_name = ? ORDER BY roll_no",
                            (class_name,))
        else:
            cur = c.execute("SELECT * FROM students ORDER BY roll_no")
        return _rows(cur)


def get_student(student_id: int) -> dict | None:
    with _session() as c:
        r = c.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        return dict(r) if r else None


def get_student_by_roll(roll_no: str) -> dict | None:
    with _session() as c:
        r = c.execute("SELECT * FROM students WHERE roll_no = ?",
                      (roll_no.strip().upper(),)).fetchone()
        return dict(r) if r else None


# --- subjects and topics ----------------------------------------------------
def add_subject(faculty_id: int, code: str, name: str, class_name: str,
                cia_weight: float = config.DEFAULT_CIA_WEIGHT, conn=None) -> int:
    code, name, class_name = code.strip().upper(), name.strip(), class_name.strip()
    if not (code and name and class_name):
        raise ValueError("Code, name and class are all required.")
    if not 0 <= cia_weight <= 1:
        raise ValueError("CIA weight must be between 0 and 1.")
    with _session(conn) as c:
        try:
            return c.execute(
                "INSERT INTO subjects (faculty_id, code, name, class_name, cia_weight) "
                "VALUES (?, ?, ?, ?, ?)",
                (faculty_id, code, name, class_name, cia_weight)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateError(f"{code} already exists for {class_name}.") from exc


def add_topic(subject_id: int, unit_no: int, title: str, conn=None) -> int:
    title = title.strip()
    if not title:
        raise ValueError("Topic title is required.")
    with _session(conn) as c:
        return c.execute(
            "INSERT INTO topics (subject_id, unit_no, title) VALUES (?, ?, ?)",
            (subject_id, unit_no, title)).lastrowid


def list_subjects(class_name: str | None = None, faculty_id: int | None = None) -> list[dict]:
    """Subjects with their faculty name, optionally filtered, ordered by code."""
    sql = ("SELECT s.*, f.name AS faculty_name FROM subjects s "
           "JOIN faculty f ON f.id = s.faculty_id")
    clauses, args = [], []
    if class_name is not None:
        clauses.append("s.class_name = ?")
        args.append(class_name)
    if faculty_id is not None:
        clauses.append("s.faculty_id = ?")
        args.append(faculty_id)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    with _session() as c:
        return _rows(c.execute(sql + " ORDER BY s.code", args))


def list_topics(subject_id: int, conn=None) -> list[dict]:
    with _session(conn) as c:
        return _rows(c.execute(
            "SELECT * FROM topics WHERE subject_id = ? ORDER BY unit_no, id", (subject_id,)))


def create_subject_with_topics(faculty_id: int, code: str, name: str, class_name: str,
                               cia_weight: float, topics: list[tuple[int, str]]) -> int:
    """Create a subject and its topics in one transaction (all or nothing)."""
    with _session() as c:
        subject_id = add_subject(faculty_id, code, name, class_name, cia_weight, conn=c)
        for unit_no, title in topics:
            add_topic(subject_id, unit_no, title, conn=c)
        return subject_id


def update_topics(subject_id: int, rows: list[dict]) -> None:
    """Make the subject's topics match ``rows`` (dicts with id/unit_no/title).

    Rows with an id of this subject are renamed, rows without one are added,
    and existing topics missing from ``rows`` are deleted. Questions pointing
    at a deleted topic are untagged by the ``ON DELETE SET NULL`` foreign key
    on ``questions.topic_id`` (SAN-122 must declare it that way).
    """
    with _session() as c:
        existing = {r[0] for r in c.execute(
            "SELECT id FROM topics WHERE subject_id = ?", (subject_id,))}
        keep = set()
        for r in rows:
            title = str(r["title"]).strip()
            if not title:
                raise ValueError("Topic title is required.")
            tid = r.get("id")
            if tid is not None and int(tid) in existing:
                keep.add(int(tid))
                c.execute("UPDATE topics SET unit_no = ?, title = ? WHERE id = ?",
                          (int(r["unit_no"]), title, int(tid)))
            else:
                add_topic(subject_id, int(r["unit_no"]), title, conn=c)
        for tid in existing - keep:
            c.execute("DELETE FROM topics WHERE id = ?", (tid,))


def list_subject_summaries(faculty_id: int) -> list[dict]:
    """A faculty member's own subjects with enrolled-student and topic counts."""
    with _session() as c:
        return _rows(c.execute(
            "SELECT s.*, "
            "(SELECT COUNT(*) FROM enrollments e WHERE e.subject_id = s.id) AS student_count, "
            "(SELECT COUNT(*) FROM topics t WHERE t.subject_id = s.id) AS topic_count "
            "FROM subjects s WHERE s.faculty_id = ? ORDER BY s.code", (faculty_id,)))


# --- enrollments ------------------------------------------------------------
def _check_target(target: float | None) -> float | None:
    if target is None:
        return None
    if not config.TARGET_MIN <= target <= config.TARGET_MAX:
        raise ValueError(
            f"Target must be between {config.TARGET_MIN} and {config.TARGET_MAX}.")
    return float(target)


def enroll(student_id: int, subject_id: int, target: float | None = None, conn=None) -> None:
    """Enroll (idempotent). A given target is saved; None keeps any existing one."""
    target = _check_target(target)
    with _session(conn) as c:
        c.execute("INSERT OR IGNORE INTO enrollments (student_id, subject_id, target) "
                  "VALUES (?, ?, ?)", (student_id, subject_id, target))
        if target is not None:
            c.execute("UPDATE enrollments SET target = ? WHERE student_id = ? AND subject_id = ?",
                      (target, student_id, subject_id))


def set_target(student_id: int, subject_id: int, target: float) -> None:
    target = _check_target(target)
    if target is None:
        raise ValueError("Target is required.")
    with _session() as c:
        cur = c.execute("UPDATE enrollments SET target = ? "
                        "WHERE student_id = ? AND subject_id = ?",
                        (target, student_id, subject_id))
        if cur.rowcount == 0:
            raise ValueError("Enroll in the subject before setting a target.")


def get_enrollment(student_id: int, subject_id: int) -> dict | None:
    with _session() as c:
        r = c.execute("SELECT * FROM enrollments WHERE student_id = ? AND subject_id = ?",
                      (student_id, subject_id)).fetchone()
        return dict(r) if r else None


def list_enrollments(student_id: int) -> list[dict]:
    with _session() as c:
        return _rows(c.execute(
            "SELECT * FROM enrollments WHERE student_id = ? ORDER BY subject_id", (student_id,)))


def list_subject_enrollments(subject_id: int) -> list[dict]:
    """Enrolled students of a subject with their targets."""
    with _session() as c:
        return _rows(c.execute(
            "SELECT e.target, st.* FROM enrollments e JOIN students st ON st.id = e.student_id "
            "WHERE e.subject_id = ? ORDER BY st.roll_no", (subject_id,)))


# --- papers and marks -------------------------------------------------------
def list_questions(subject_id: int, component: str) -> list[dict]:
    with _session() as c:
        return _rows(c.execute(
            "SELECT * FROM questions WHERE subject_id = ? AND component = ? ORDER BY q_no",
            (subject_id, component)))


def save_paper(subject_id: int, component: str, rows: list[dict], conn=None) -> None:
    """Make the paper match ``rows`` (dicts with q_no, max_marks, topic_id).

    Questions are matched by q_no: existing ones are updated in place (so
    their marks stay), new ones are added, and removed ones are deleted with
    their marks (``ON DELETE CASCADE`` on ``marks.question_id``).
    """
    with _session(conn) as c:
        existing = {r["q_no"]: r["id"] for r in c.execute(
            "SELECT id, q_no FROM questions WHERE subject_id = ? AND component = ?",
            (subject_id, component))}
        keep = set()
        for r in rows:
            q_no, mx, topic = int(r["q_no"]), float(r["max_marks"]), r.get("topic_id")
            topic = None if topic is None else int(topic)
            if q_no in keep:
                raise DuplicateError(f"Question number {q_no} is used twice.")
            keep.add(q_no)
            if q_no in existing:
                c.execute("UPDATE questions SET max_marks = ?, topic_id = ? WHERE id = ?",
                          (mx, topic, existing[q_no]))
            else:
                c.execute("INSERT INTO questions (subject_id, component, q_no, max_marks, topic_id) "
                          "VALUES (?, ?, ?, ?, ?)", (subject_id, component, q_no, mx, topic))
        for q_no, qid in existing.items():
            if q_no not in keep:
                c.execute("DELETE FROM questions WHERE id = ?", (qid,))


def list_marks(subject_id: int, component: str) -> list[dict]:
    with _session() as c:
        return _rows(c.execute(
            "SELECT m.question_id, m.roll_no, m.score FROM marks m "
            "JOIN questions q ON q.id = m.question_id "
            "WHERE q.subject_id = ? AND q.component = ? ORDER BY q.q_no, m.roll_no",
            (subject_id, component)))


def save_marks(subject_id: int, component: str,
               records: list[tuple[int, str, float | None]], conn=None) -> None:
    """Replace every mark of a paper. ``records`` are (question_id, roll_no, score|None)."""
    with _session(conn) as c:
        c.execute("DELETE FROM marks WHERE question_id IN "
                  "(SELECT id FROM questions WHERE subject_id = ? AND component = ?)",
                  (subject_id, component))
        c.executemany("INSERT INTO marks (question_id, roll_no, score) VALUES (?, ?, ?)", records)


def list_ese_marks(subject_id: int) -> list[dict]:
    with _session() as c:
        return _rows(c.execute(
            "SELECT roll_no, score FROM ese_marks WHERE subject_id = ? ORDER BY roll_no",
            (subject_id,)))


def save_ese_marks(subject_id: int, records: list[tuple[str, float]], conn=None) -> None:
    """Replace the subject's ESE totals. ``records`` are (roll_no, score)."""
    with _session(conn) as c:
        c.execute("DELETE FROM ese_marks WHERE subject_id = ?", (subject_id,))
        c.executemany("INSERT INTO ese_marks (subject_id, roll_no, score) VALUES (?, ?, ?)",
                      [(subject_id, r, s) for r, s in records])


# --- silly-error flags (SAN-124) --------------------------------------------
register_table("""CREATE TABLE IF NOT EXISTS silly_flags (
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        PRIMARY KEY (student_id, question_id)
    )""")


def set_silly_flag(student_id: int, question_id: int, conn=None) -> None:
    """Flag a question as a calculation/silly slip for a student (idempotent)."""
    with _session(conn) as c:
        c.execute("INSERT OR IGNORE INTO silly_flags (student_id, question_id) VALUES (?, ?)",
                  (student_id, question_id))


def clear_silly_flag(student_id: int, question_id: int, conn=None) -> None:
    with _session(conn) as c:
        c.execute("DELETE FROM silly_flags WHERE student_id = ? AND question_id = ?",
                  (student_id, question_id))


def get_silly_flags(student_id: int, subject_id: int) -> set[int]:
    """Question ids the student flagged in this subject (every component)."""
    with _session() as c:
        return {r[0] for r in c.execute(
            "SELECT f.question_id FROM silly_flags f JOIN questions q ON q.id = f.question_id "
            "WHERE f.student_id = ? AND q.subject_id = ?", (student_id, subject_id))}


def count_silly_flags(subject_id: int, component: str) -> list[dict]:
    """[{question_id, q_no, flags}] for every question of a paper, in q_no order."""
    with _session() as c:
        return _rows(c.execute(
            "SELECT q.id AS question_id, q.q_no, COUNT(f.student_id) AS flags "
            "FROM questions q LEFT JOIN silly_flags f ON f.question_id = q.id "
            "WHERE q.subject_id = ? AND q.component = ? GROUP BY q.id ORDER BY q.q_no",
            (subject_id, component)))
