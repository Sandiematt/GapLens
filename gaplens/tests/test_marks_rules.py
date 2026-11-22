"""Pure marks-entry rules: paper validation, table/CSV -> records."""
import math

from core import marks_rules as mr

QS = [{"id": 11, "q_no": 1, "max_marks": 5.0},
      {"id": 12, "q_no": 2, "max_marks": 10.0}]


# --- paper structure --------------------------------------------------------
def test_maxima_warning_when_total_differs():
    rows = [{"q_no": 1, "max_marks": 5}, {"q_no": 2, "max_marks": 19}]
    msg = mr.maxima_warning(rows, 25)
    assert "24" in msg and "25" in msg


def test_maxima_warning_none_when_total_matches():
    rows = [{"q_no": 1, "max_marks": 12.5}, {"q_no": 2, "max_marks": 12.5}]
    assert mr.maxima_warning(rows, 25) is None


def test_paper_needs_questions_unique_numbers_and_positive_max():
    assert mr.validate_paper([]) != []
    dup = [{"q_no": 1, "max_marks": 5}, {"q_no": 1, "max_marks": 5}]
    assert any("twice" in e or "duplicate" in e.lower() for e in mr.validate_paper(dup))
    bad = [{"q_no": 1, "max_marks": 0}, {"q_no": None, "max_marks": 5}]
    assert len(mr.validate_paper(bad)) == 2
    assert mr.validate_paper([{"q_no": 1, "max_marks": 5}, {"q_no": 2, "max_marks": 2.5}]) == []


# --- table -> records -------------------------------------------------------
def test_table_blank_cell_is_none_and_zero_is_zero():
    rows = [{"roll_no": "25MCA001", "Q1": 0, "Q2": None}]
    records, errors = mr.table_to_records(rows, QS)
    assert errors == []
    assert records == [(11, "25MCA001", 0.0), (12, "25MCA001", None)]


def test_table_skips_rows_blank_in_every_cell():
    rows = [{"roll_no": "25MCA001", "Q1": None, "Q2": float("nan")},
            {"roll_no": "25MCA002", "Q1": "", "Q2": "  "},
            {"roll_no": "25MCA003", "Q1": 4, "Q2": None}]
    records, errors = mr.table_to_records(rows, QS)
    assert errors == []
    assert {r[1] for r in records} == {"25MCA003"}


def test_table_rejects_out_of_range_with_clear_message_and_no_records():
    rows = [{"roll_no": "25mca003", "Q1": 6, "Q2": -1}, {"roll_no": "25MCA004", "Q1": 1, "Q2": 1}]
    records, errors = mr.table_to_records(rows, QS)
    assert records == []
    assert "25MCA003 Q1: 6 is above the 5-mark maximum" in errors
    assert any("Q2" in e and "below 0" in e for e in errors)


def test_table_rejects_non_numeric_and_nan_text():
    rows = [{"roll_no": "25MCA001", "Q1": "abc", "Q2": "nan"}]
    records, errors = mr.table_to_records(rows, QS)
    assert records == [] and len(errors) == 2


def test_table_keeps_unknown_roll_numbers():
    rows = [{"roll_no": "99XYZ001", "Q1": 3, "Q2": 4}]
    records, errors = mr.table_to_records(rows, QS)
    assert errors == [] and len(records) == 2


def test_table_row_with_marks_but_no_roll_is_an_error():
    records, errors = mr.table_to_records([{"roll_no": " ", "Q1": 3, "Q2": None}], QS)
    assert records == [] and errors


def test_table_duplicate_roll_is_an_error():
    rows = [{"roll_no": "A1", "Q1": 1, "Q2": 1}, {"roll_no": "a1", "Q1": 2, "Q2": 2}]
    records, errors = mr.table_to_records(rows, QS)
    assert records == [] and any("more than once" in e for e in errors)


# --- ESE ---------------------------------------------------------------------
def test_ese_records_validate_0_to_100_and_skip_blank_rows():
    rows = [{"roll_no": "25MCA001", "score": 55.5}, {"roll_no": "25MCA002", "score": None},
            {"roll_no": "25MCA003", "score": 0}]
    records, errors = mr.ese_table_to_records(rows)
    assert errors == [] and records == [("25MCA001", 55.5), ("25MCA003", 0.0)]
    records, errors = mr.ese_table_to_records([{"roll_no": "25MCA001", "score": 101}])
    assert records == [] and "101" in errors[0] and "100" in errors[0]


# --- CSV ---------------------------------------------------------------------
def test_template_has_roll_and_question_columns_and_enrolled_rolls():
    text = mr.template_csv(["25MCA001", "25MCA002"], QS)
    lines = text.strip().splitlines()
    assert lines[0] == "roll_no,Q1,Q2"
    assert lines[1] == "25MCA001,," and len(lines) == 3


def test_ese_template():
    assert mr.ese_template_csv(["A1"]).strip().splitlines() == ["roll_no,ese", "A1,"]


def test_template_round_trips_through_parse_and_save_rules():
    text = "roll_no,Q1,Q2\n25MCA001,5,\n25MCA002,,\n25MCA003,2,9.5\n"
    rows, errors = mr.parse_marks_csv(text.encode("utf-8-sig"), QS)
    assert errors == []
    records, errors = mr.table_to_records(rows, QS)
    assert errors == []
    assert records == [(11, "25MCA001", 5.0), (12, "25MCA001", None),
                       (11, "25MCA003", 2.0), (12, "25MCA003", 9.5)]


def test_parse_csv_reports_missing_and_unknown_columns():
    _, errors = mr.parse_marks_csv(b"roll_no,Q1\nA,1\n", QS)
    assert any("Q2" in e for e in errors)
    _, errors = mr.parse_marks_csv(b"roll_no,Q1,Q2,Q9\nA,1,1,1\n", QS)
    assert any("Q9" in e for e in errors)
    _, errors = mr.parse_marks_csv(b"name,Q1,Q2\nA,1,1\n", QS)
    assert any("roll_no" in e for e in errors)


def test_parse_csv_ignores_name_column_and_header_case():
    rows, errors = mr.parse_marks_csv(b"ROLL_NO,Name,q1,Q2\nA1,Ann,3,4\n", QS)
    assert errors == [] and rows == [{"roll_no": "A1", "Q1": "3", "Q2": "4"}]


def test_parse_ese_csv():
    rows, errors = mr.parse_ese_csv(b"roll_no,ese\nA1,60\nA2,\n")
    assert errors == [] and rows == [{"roll_no": "A1", "score": "60"},
                                     {"roll_no": "A2", "score": ""}]
    _, errors = mr.parse_ese_csv(b"roll_no,marks\nA1,60\n")
    assert errors


# --- grid --------------------------------------------------------------------
def test_grid_lists_students_then_anonymous_rows_with_blank_for_missing():
    students = [{"roll_no": "A1", "name": "Ann"}, {"roll_no": "A2", "name": "Bo"}]
    marks = [{"question_id": 11, "roll_no": "A1", "score": 4.0},
             {"question_id": 12, "roll_no": "A1", "score": None},
             {"question_id": 11, "roll_no": "ZZ9", "score": 1.0}]
    grid = mr.marks_grid(students, QS, marks)
    assert [g["roll_no"] for g in grid] == ["A1", "A2", "ZZ9"]
    assert grid[0]["Q1"] == 4.0 and grid[0]["Q2"] is None
    assert grid[1]["Q1"] is None
    assert grid[2]["name"] == mr.ANONYMOUS_NAME


def test_total_ignores_blank():
    assert mr.row_total({"Q1": 4.0, "Q2": None}, QS) == 4.0
    assert math.isclose(mr.row_total({"Q1": 4.5, "Q2": 1}, QS), 5.5)
