"""Pure subject/topic rules: parsing typed topic lines and validation."""
from __future__ import annotations

import re

_UNIT_LINE = re.compile(r"^\s*(?:unit\s*)?(\d+)\s*\|\s*(.+?)\s*$", re.IGNORECASE)


def parse_topic_lines(text: str) -> list[tuple[int, str]]:
    """Parse one topic per line, ``unit | topic`` with an optional unit prefix.

    A line without a numeric prefix joins the previous line's unit (unit 1 at the start).
    """
    out: list[tuple[int, str]] = []
    unit = 1
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = _UNIT_LINE.match(line)
        if m:
            unit, title = int(m.group(1)), m.group(2)
        else:
            title = line
        out.append((unit, title))
    return out


def _duplicate_titles(titles: list[str]) -> list[str]:
    seen, dups = set(), []
    for t in titles:
        key = t.strip().casefold()
        if key in seen and t.strip() not in dups:
            dups.append(t.strip())
        seen.add(key)
    return dups


def validate_subject(code: str, name: str, class_name: str, cia_pct: float,
                     topics: list[tuple[int, str]]) -> list[str]:
    errors = []
    if not (code or "").strip():
        errors.append("Enter a subject code.")
    if not (name or "").strip():
        errors.append("Enter a subject name.")
    if not (class_name or "").strip():
        errors.append("Enter a class.")
    if cia_pct is None or not 0 <= cia_pct <= 100:
        errors.append("CIA weight must be between 0 and 100.")
    if not topics:
        errors.append(NEED_A_TOPIC)
    for d in _duplicate_titles([t for _, t in topics]):
        errors.append(f'Topic "{d}" is listed more than once.')
    return errors


NEED_A_TOPIC = "Add at least one topic."


def validate_topic_rows(rows: list[dict]) -> list[str]:
    """Errors in an edited topic table; a subject needs at least one topic."""
    errors = [] if rows else [NEED_A_TOPIC]
    for i, r in enumerate(rows, 1):
        if not str(r.get("title") or "").strip():
            errors.append(f"Row {i}: topic title is empty.")
        unit = r.get("unit_no")
        if unit is None or unit != unit or int(unit) < 1:
            errors.append(f"Row {i}: unit must be a number from 1.")
    for d in _duplicate_titles([str(r.get("title") or "") for r in rows
                                if str(r.get("title") or "").strip()]):
        errors.append(f'Topic "{d}" is listed more than once.')
    return errors
