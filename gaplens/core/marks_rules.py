"""Pure rules for paper structure and marks entry. No I/O, no Streamlit.

Questions are dicts with ``id``, ``q_no`` and ``max_marks``. A marks table is
a list of row dicts with ``roll_no`` and one ``Q<n>`` key per question.
"""
from __future__ import annotations

import csv
import io
import math

import config

ANONYMOUS_NAME = "(not in class list)"


def qcol(q_no: int) -> str:
    return f"Q{int(q_no)}"


def _fmt(x: float) -> str:
    return f"{x:g}"


def _blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return type(v).__name__ == "NAType"  # pandas NA


def _num(v) -> float | None:
    """Parse a cell; None if it is not a finite number."""
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


# --- paper structure ---------------------------------------------------------
def maxima_warning(rows: list[dict], component_total: float) -> str | None:
    total = sum(float(r["max_marks"]) for r in rows if not _blank(r.get("max_marks"))
                and _num(r["max_marks"]) is not None)
    if math.isclose(total, component_total):
        return None
    diff = component_total - total
    hint = (f"Add {_fmt(diff)} mark{'s' if abs(diff) != 1 else ''} to a question or add a question."
            if diff > 0 else f"Remove {_fmt(-diff)} mark{'s' if abs(diff) != 1 else ''}.")
    return (f"Maximum marks add up to {_fmt(total)}, but this component is out of "
            f"{_fmt(component_total)}. {hint}")


def validate_paper(rows: list[dict]) -> list[str]:
    if not rows:
        return ["Add at least one question."]
    errors, seen = [], set()
    for i, r in enumerate(rows, start=1):
        q = _num(r.get("q_no")) if not _blank(r.get("q_no")) else None
        label = f"Row {i}"
        if q is None or q < 1 or q != int(q):
            errors.append(f"{label}: question number must be a whole number from 1.")
        else:
            if int(q) in seen:
                errors.append(f"Question number {int(q)} is used twice.")
            seen.add(int(q))
            label = f"Q{int(q)}"
        m = _num(r.get("max_marks")) if not _blank(r.get("max_marks")) else None
        if m is None or m <= 0:
            errors.append(f"{label}: max marks must be a number above 0.")
    return errors


# --- table -> records ---------------------------------------------------------
def _rows_to_records(rows, columns):
    """``columns``: list of (key, label, id, max). Returns (records, errors)."""
    records, errors, seen = [], [], set()
    for row in rows:
        roll = "" if _blank(row.get("roll_no")) else str(row["roll_no"]).strip().upper()
        cells = [row.get(key) for key, *_ in columns]
        if all(_blank(c) for c in cells):
            continue  # not entered
        if not roll:
            errors.append("A row has marks but no roll number.")
            continue
        if roll in seen:
            errors.append(f"Roll number {roll} appears more than once.")
            continue
        seen.add(roll)
        for (key, label, qid, mx), cell in zip(columns, cells):
            if _blank(cell):
                records.append((qid, roll, None))
                continue
            x = _num(cell)
            if x is None:
                errors.append(f"{roll} {label}: '{cell}' is not a number.")
            elif x < 0:
                errors.append(f"{roll} {label}: {_fmt(x)} is below 0.")
            elif x > mx:
                errors.append(f"{roll} {label}: {_fmt(x)} is above the {_fmt(mx)}-mark maximum")
            else:
                records.append((qid, roll, x))
    return ([], errors) if errors else (records, [])


def table_to_records(rows: list[dict], questions: list[dict]):
    cols = [(qcol(q["q_no"]), qcol(q["q_no"]), q["id"], float(q["max_marks"]))
            for q in questions]
    return _rows_to_records(rows, cols)


def ese_table_to_records(rows: list[dict]):
    records, errors = _rows_to_records(rows, [("score", "ESE", None, float(config.COMPONENTS["ESE"]))])
    return [(roll, score) for _, roll, score in records], errors


# --- CSV ----------------------------------------------------------------------
def _csv_text(lines: list[list[str]]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(lines)
    return buf.getvalue()


def template_csv(rolls: list[str], questions: list[dict]) -> str:
    cols = [qcol(q["q_no"]) for q in questions]
    return _csv_text([["roll_no", *cols]] + [[r] + [""] * len(cols) for r in rolls])


def ese_template_csv(rolls: list[str]) -> str:
    return _csv_text([["roll_no", "ese"]] + [[r, ""] for r in rolls])


def _read_csv(data: bytes | str):
    text = data.decode("utf-8-sig", errors="replace") if isinstance(data, bytes) else data
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return None, []
    header = [h.strip().lower() for h in rows[0]]
    return header, [dict(zip(header, (c.strip() for c in r))) for r in rows[1:]]


def parse_marks_csv(data: bytes | str, questions: list[dict]):
    """CSV -> (table rows, errors). Needs roll_no plus every question column."""
    header, body = _read_csv(data)
    if header is None:
        return [], ["The file is empty."]
    errors = []
    if "roll_no" not in header:
        errors.append("The file needs a roll_no column.")
    wanted = {qcol(q["q_no"]).lower(): qcol(q["q_no"]) for q in questions}
    for low, name in wanted.items():
        if low not in header:
            errors.append(f"Column {name} is missing. Download the template for this paper.")
    for h in header:
        if h not in wanted and h not in ("roll_no", "name", "total", ""):
            errors.append(f"Column {h.upper()} is not a question of this paper.")
    if errors:
        return [], errors
    return [{"roll_no": r.get("roll_no", ""),
             **{name: r.get(low, "") for low, name in wanted.items()}} for r in body], []


def parse_ese_csv(data: bytes | str):
    header, body = _read_csv(data)
    if header is None:
        return [], ["The file is empty."]
    if "roll_no" not in header or "ese" not in header:
        return [], ["The file needs roll_no and ese columns."]
    return [{"roll_no": r.get("roll_no", ""), "score": r.get("ese", "")} for r in body], []


# --- grid ---------------------------------------------------------------------
def marks_grid(students: list[dict], questions: list[dict], marks: list[dict]) -> list[dict]:
    """One row per enrolled student, then one per unmatched roll number saved earlier."""
    by_cell = {(m["question_id"], m["roll_no"]): m["score"] for m in marks}
    names = {s["roll_no"]: s["name"] for s in students}
    rolls = [s["roll_no"] for s in students]
    rolls += sorted({m["roll_no"] for m in marks} - set(rolls))
    return [{"roll_no": r, "name": names.get(r, ANONYMOUS_NAME),
             **{qcol(q["q_no"]): by_cell.get((q["id"], r)) for q in questions}} for r in rolls]


def row_total(row: dict, questions: list[dict]) -> float:
    return sum(x for q in questions if (x := _num(row.get(qcol(q["q_no"])))) is not None)
