from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from src.models import ExerciseEntry, GlucoseEntry, MealType

_DATE_PATTERN = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\w{3}) (\d{1,2}), (\d{4})"
)
_GLUCOSE_PATTERN = re.compile(r"^(\d+) mg/dL$")
_EXERCISE_PATTERN = re.compile(r"^(\d+) min \u2022 (\d+) BPM$")

_MONTH_ABBR = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


@dataclass
class ParseResult:
    glucose_entries: list[GlucoseEntry] = field(default_factory=list)
    exercise_entries: list[ExerciseEntry] = field(default_factory=list)
    available_dates: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _parse_iso_date(match: re.Match[str]) -> str:
    """Convert a regex match from _DATE_PATTERN to an ISO date string."""
    month_str, day_str, year_str = match.group(2), match.group(3), match.group(4)
    month = _MONTH_ABBR[month_str]
    return f"{int(year_str):04d}-{month:02d}-{int(day_str):02d}"


def _classify_row(row: Sequence[str | None]) -> tuple[str, list[str]]:
    """Classify a table row as 'header', 'data', or 'skip'.

    Returns (row_type, non-None values).
    """
    values = [v for v in row if v is not None]
    if not values:
        return ("skip", [])

    # Data rows have exactly 6 non-None values
    if len(values) == 6:
        return ("data", values)

    # Header rows: single long value containing a date pattern
    if len(values) == 1:
        match = _DATE_PATTERN.search(values[0])
        if match:
            return ("header", values)

    return ("skip", values)


def _parse_glucose_value(s: str) -> int | None:
    """Parse '117 mg/dL' to int 117. Returns None if unparseable."""
    match = _GLUCOSE_PATTERN.match(s.strip())
    if match:
        return int(match.group(1))
    return None


def _parse_exercise_details(s: str) -> tuple[int, int] | None:
    """Parse '33 min • 88 BPM' to (33, 88). Returns None if unparseable."""
    match = _EXERCISE_PATTERN.match(s.strip())
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def parse_pdf(pdf_path: Path) -> ParseResult:
    """Parse a Dexcom Clarity PDF and return glucose/exercise entries.

    Iterates all pages, processing tables[0] on each page. Tracks the
    current date from header rows. Creates GlucoseEntry (with meal_type
    defaulting to BREAKFAST) and ExerciseEntry objects from data rows.
    """
    result = ParseResult()
    current_date: str | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue

            table = tables[0]
            for row in table:
                row_type, values = _classify_row(row)

                if row_type == "header":
                    match = _DATE_PATTERN.search(values[0])
                    if match:
                        current_date = _parse_iso_date(match)

                elif row_type == "data":
                    if current_date is None:
                        result.warnings.append(
                            f"Page {page_num + 1}: data row before any date header: {values}"
                        )
                        continue

                    time_str = values[0]
                    event_type = values[2]
                    details = values[3]
                    glucose_str = values[5]

                    glucose = _parse_glucose_value(glucose_str)
                    if glucose is None:
                        result.warnings.append(
                            f"Page {page_num + 1}: could not parse glucose from '{glucose_str}'"
                        )
                        continue

                    if event_type == "Meal":
                        entry = GlucoseEntry(
                            date=current_date,
                            time=time_str,
                            glucose_reading=glucose,
                            food_item=details,
                            meal_type=MealType.BREAKFAST,
                        )
                        result.glucose_entries.append(entry)

                    elif event_type == "Walking":
                        exercise = _parse_exercise_details(details)
                        if exercise is None:
                            result.warnings.append(
                                f"Page {page_num + 1}: could not parse exercise details '{details}'"
                            )
                            continue
                        duration, bpm = exercise
                        entry_ex = ExerciseEntry(
                            date=current_date,
                            time=time_str,
                            activity_type="Walking",
                            duration_minutes=duration,
                            heart_rate_bpm=bpm,
                            glucose_reading=glucose,
                        )
                        result.exercise_entries.append(entry_ex)

                    else:
                        result.warnings.append(
                            f"Page {page_num + 1}: unknown event type '{event_type}'"
                        )

    # Build available_dates from actual entries (sorted ascending)
    dates_seen: set[str] = set()
    for ge in result.glucose_entries:
        dates_seen.add(ge.date)
    for ee in result.exercise_entries:
        dates_seen.add(ee.date)
    result.available_dates = sorted(dates_seen)

    return result


def filter_by_dates(
    result: ParseResult, selected_dates: list[str]
) -> ParseResult:
    """Return a new ParseResult filtered to only the selected dates."""
    date_set = set(selected_dates)
    return ParseResult(
        glucose_entries=[
            e for e in result.glucose_entries if e.date in date_set
        ],
        exercise_entries=[
            e for e in result.exercise_entries if e.date in date_set
        ],
        available_dates=sorted(d for d in result.available_dates if d in date_set),
        warnings=list(result.warnings),
    )
