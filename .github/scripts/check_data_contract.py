"""Data contract for ``data/processed/customers_clean_*.csv`` (specs/ontology.md, sections 3.1 and 3.2).

Fails when a cleaned dataset breaks the schema, domain bounds, or flag formulas defined in the
ontology, or when a raw sentinel value (AGENTS.md section 5.2) leaks into processed data.
Optional ontology flags are validated only when the column exists, so the contract grows with the
dataset version (v1, v2, ...).

Uses only the standard library so it runs without installing project dependencies.

Usage:
    python .github/scripts/check_data_contract.py [FILE ...]
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from ci_utils import REPO_ROOT, Reporter

EXPECTED_ROWS = 10_000
CORE_COLUMNS = [
    "customer_id", "name", "gender", "age", "city", "signup_date", "last_purchase_date",
    "purchase_amount", "feedback_score", "email", "phone_number", "country",
]
GENDERS = {"Male", "Female", "Unknown"}
COUNTRIES = {"USA", "Australia", "Canada", "UK", "India", "Unknown"}
NON_INDIAN_COUNTRIES = {"USA", "Australia", "Canada", "UK"}
CITIES = {"Hyderabad", "Mumbai", "Pune", "Bangalore", "Chennai", "Delhi", "Ahmedabad", "Kolkata", "Unknown"}
FEEDBACK_VALUES = {1.0, 2.0, 3.0, 4.0, 5.0, 10.0}
# specs/ontology.md 3.1: observed dates run from 2020-08-06 to 2026-01-26; reject pre-2020 or future dates.
DATE_MIN, DATE_MAX = date(2020, 1, 1), date.today()
# Text sentinels that must never survive cleaning. Numeric sentinels (-5, 200, -999, -1, 0)
# are caught by the domain bounds and regex rules below.
TEXT_SENTINELS = {"N/A", "-999", "not_a_date", "missing", "abc123"}

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
CUSTOMER_ID = re.compile(r"^C\d{5}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\d{10}$")
MAX_EXAMPLES = 3


def to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def to_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def to_bool(value: str) -> bool | None:
    return {"True": True, "False": False}.get(value)


def check_file(path: Path, reporter: Reporter) -> None:
    rel_path = path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else str(path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)

    # --- Schema -------------------------------------------------------------------------------
    missing = [col for col in CORE_COLUMNS if col not in columns]
    if missing:
        reporter.error(f"missing core columns: {missing}", file=rel_path)
        return
    bad_names = [col for col in columns if not SNAKE_CASE.match(col)]
    if bad_names:
        reporter.error(f"column names are not snake_case: {bad_names}", file=rel_path)
    if len(set(columns)) != len(columns):
        reporter.error("duplicated column names", file=rel_path)
    if len(rows) != EXPECTED_ROWS:
        reporter.error(f"expected {EXPECTED_ROWS:,} rows, found {len(rows):,}", file=rel_path)

    violations: dict[str, list[str]] = defaultdict(list)

    def flag(rule: str, line: int, value: object) -> None:
        violations[rule].append(f"line {line}={value!r}")

    def expect_flag(column: str, row: dict[str, str], line: int, expected: bool) -> None:
        if column in columns and to_bool(row[column]) is not expected:
            flag(f"{column} does not match its ontology formula", line, row[column])

    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        line = index + 2  # header is line 1

        for column, value in row.items():
            if value in TEXT_SENTINELS:
                flag(f"raw sentinel left in '{column}'", line, value)

        # --- Identity -----------------------------------------------------------------------
        cid = row["customer_id"]
        if cid != f"C{index + 1:05d}":
            flag("customer_id is not the sequential C00001..C10000 key", line, cid)
        if not CUSTOMER_ID.match(cid) or cid in seen_ids:
            flag("customer_id is malformed or duplicated", line, cid)
        seen_ids.add(cid)
        if not row["name"]:
            flag("name is blank (expected 'Unknown')", line, row["name"])

        # --- Categoricals -------------------------------------------------------------------
        for column, allowed in (("gender", GENDERS), ("country", COUNTRIES), ("city", CITIES)):
            if row[column] not in allowed:
                flag(f"{column} outside its taxonomy", line, row[column])

        # --- Numeric domains ----------------------------------------------------------------
        age, amount, score = (to_float(row[c]) if row[c] else None for c in ("age", "purchase_amount", "feedback_score"))
        if row["age"] and (age is None or not 18 <= age <= 100):
            flag("age outside [18, 100]", line, row["age"])
        if row["purchase_amount"] and (amount is None or not 0 < amount <= 10_000):
            flag("purchase_amount outside (0, 10000]", line, row["purchase_amount"])
        if row["feedback_score"] and score not in FEEDBACK_VALUES:
            flag("feedback_score outside {1..5, 10}", line, row["feedback_score"])

        # --- Dates ----------------------------------------------------------------------------
        dates = {}
        for column in ("signup_date", "last_purchase_date"):
            value = row[column]
            parsed = to_date(value) if value else None
            if value and (parsed is None or not DATE_MIN <= parsed <= DATE_MAX):
                flag(f"{column} is not an ISO date in [{DATE_MIN}, {DATE_MAX}]", line, value)
            dates[column] = parsed

        # --- Contact channels ---------------------------------------------------------------
        if row["email"] and not EMAIL.match(row["email"]):
            flag("email fails the ontology regex", line, row["email"])
        if row["phone_number"] and not PHONE.match(row["phone_number"]):
            flag("phone_number is not 10 digits", line, row["phone_number"])

        # --- Data-quality flags (ontology 3.2) ----------------------------------------------
        signup, last = dates["signup_date"], dates["last_purchase_date"]
        expect_flag("has_valid_email", row, line, bool(row["email"]))
        expect_flag("has_valid_phone", row, line, bool(row["phone_number"]))
        expect_flag("is_date_inverted", row, line, bool(signup and last and last < signup))
        expect_flag("is_age_missing", row, line, not row["age"])
        expect_flag("is_purchase_missing", row, line, not row["purchase_amount"])
        expect_flag("is_score_10_spike", row, line, score == 10.0)
        expect_flag("is_geo_mismatch", row, line, row["city"] != "Unknown" and row["country"] in NON_INDIAN_COUNTRIES)
        if "feedback_score_1_to_5" in columns:
            normalized = to_float(row["feedback_score_1_to_5"]) if row["feedback_score_1_to_5"] else None
            expected = score if score is not None and score <= 5 else None
            if normalized != expected:
                flag("feedback_score_1_to_5 does not match its ontology formula", line, row["feedback_score_1_to_5"])
        if "completeness_score" in columns:
            completeness = to_float(row["completeness_score"])
            if completeness is None or not 0.0 <= completeness <= 1.0:
                flag("completeness_score outside [0, 1]", line, row["completeness_score"])

    for rule, examples in violations.items():
        shown = ", ".join(examples[:MAX_EXAMPLES])
        reporter.error(f"{rule}: {len(examples)} row(s), e.g. {shown}", file=rel_path)
    if not violations and not missing:
        optional = [c for c in columns if c not in CORE_COLUMNS]
        reporter.ok(f"{rel_path}: {len(rows):,} rows, {len(columns)} columns (flags checked: {optional})")


def main() -> int:
    reporter = Reporter("Data contract")
    paths = [Path(arg).resolve() for arg in sys.argv[1:]] or sorted(
        (REPO_ROOT / "data" / "processed").glob("customers_clean_*.csv")
    )
    if not paths:
        reporter.ok("no cleaned datasets yet")
    for path in paths:
        check_file(path, reporter)
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
