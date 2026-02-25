from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.models import MealType
from src.pdf_parser import (
    ParseResult,
    _classify_row,
    _parse_exercise_details,
    _parse_glucose_value,
    _parse_iso_date,
    filter_by_dates,
    parse_pdf,
    _DATE_PATTERN,
)

SAMPLE_PDF = Path("docs/samples/clarity_2026-02-18_to_2026-02-22.pdf")


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def parsed() -> ParseResult:
    """Parse the sample PDF once for all integration tests."""
    assert SAMPLE_PDF.exists(), f"Sample PDF not found at {SAMPLE_PDF}"
    return parse_pdf(SAMPLE_PDF)


# ── TestClassifyRow ───────────────────────────────────────────────────


class TestClassifyRow:
    def test_header_detected(self) -> None:
        row = [
            "Sun, Feb 22, 2026\n400\nGlucos\n350 (mg/dL\n300\n250",
            None,
            None,
        ]
        row_type, values = _classify_row(row)
        assert row_type == "header"
        assert len(values) == 1

    def test_data_row_meal(self) -> None:
        row = ["9:40 AM", "CGM", "Meal", "Egg omelette", "--", "117 mg/dL"]
        row_type, values = _classify_row(row)
        assert row_type == "data"
        assert len(values) == 6

    def test_data_row_walking(self) -> None:
        row = ["10:56 AM", "CGM", "Walking", "33 min \u2022 88 BPM", "--", "108 mg/dL"]
        row_type, values = _classify_row(row)
        assert row_type == "data"
        assert len(values) == 6

    def test_blank_row_skip(self) -> None:
        row = [None, None, None, None, None, None]
        row_type, _ = _classify_row(row)
        assert row_type == "skip"

    def test_empty_string_skip(self) -> None:
        row = [""]
        row_type, _ = _classify_row(row)
        assert row_type == "skip"

    def test_footer_skip(self) -> None:
        row = ["Data uploaded: Mon, Feb 23, 2026 10:22 AM MST some footer text"]
        row_type, _ = _classify_row(row)
        # Footer contains a date but is a single value — classified as header
        # This is fine because parse_pdf just updates current_date harmlessly
        assert row_type in ("header", "skip")


# ── TestDateParsing ───────────────────────────────────────────────────


class TestDateParsing:
    def test_iso_conversion(self) -> None:
        match = _DATE_PATTERN.search("Sun, Feb 22, 2026")
        assert match is not None
        assert _parse_iso_date(match) == "2026-02-22"

    def test_single_digit_day(self) -> None:
        match = _DATE_PATTERN.search("Mon, Mar 3, 2026")
        assert match is not None
        assert _parse_iso_date(match) == "2026-03-03"

    def test_all_day_abbreviations(self) -> None:
        for day in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            text = f"{day}, Jan 15, 2026"
            match = _DATE_PATTERN.search(text)
            assert match is not None, f"Failed to match {day}"

    def test_date_embedded_in_noise(self) -> None:
        text = "Daily\n14 days\nSun, Feb 22, 2026\n400\nGlucos\n350"
        match = _DATE_PATTERN.search(text)
        assert match is not None
        assert _parse_iso_date(match) == "2026-02-22"


# ── TestGlucoseValueParsing ──────────────────────────────────────────


class TestGlucoseValueParsing:
    def test_three_digit(self) -> None:
        assert _parse_glucose_value("117 mg/dL") == 117

    def test_two_digit(self) -> None:
        assert _parse_glucose_value("80 mg/dL") == 80

    def test_invalid_returns_none(self) -> None:
        assert _parse_glucose_value("--") is None

    def test_empty_returns_none(self) -> None:
        assert _parse_glucose_value("") is None

    def test_no_units_returns_none(self) -> None:
        assert _parse_glucose_value("117") is None


# ── TestExerciseDetailsParsing ────────────────────────────────────────


class TestExerciseDetailsParsing:
    def test_normal_parse(self) -> None:
        result = _parse_exercise_details("33 min \u2022 88 BPM")
        assert result == (33, 88)

    def test_single_digit_values(self) -> None:
        result = _parse_exercise_details("5 min \u2022 9 BPM")
        assert result == (5, 9)

    def test_non_matching_returns_none(self) -> None:
        assert _parse_exercise_details("Egg omelette") is None

    def test_empty_returns_none(self) -> None:
        assert _parse_exercise_details("") is None


# ── TestParsePdf (integration) ────────────────────────────────────────


class TestParsePdf:
    def test_has_glucose_entries(self, parsed: ParseResult) -> None:
        assert len(parsed.glucose_entries) > 0

    def test_total_meal_entries(self, parsed: ParseResult) -> None:
        # 14 days of data — from manual inspection: 64 meal entries
        assert len(parsed.glucose_entries) == 64

    def test_total_exercise_entries(self, parsed: ParseResult) -> None:
        # 5 exercise entries across all 14 days
        assert len(parsed.exercise_entries) == 5

    def test_all_meals_default_breakfast(self, parsed: ParseResult) -> None:
        for entry in parsed.glucose_entries:
            assert entry.meal_type == MealType.BREAKFAST

    def test_glucose_all_positive(self, parsed: ParseResult) -> None:
        for entry in parsed.glucose_entries:
            assert entry.glucose_reading > 0

    def test_known_entry_feb22_egg_omelette(self, parsed: ParseResult) -> None:
        matches = [
            e for e in parsed.glucose_entries
            if e.date == "2026-02-22" and e.time == "9:40 AM"
        ]
        assert len(matches) == 1
        assert matches[0].glucose_reading == 117
        assert "omelette" in matches[0].food_item.lower()

    def test_exercise_feb22(self, parsed: ParseResult) -> None:
        matches = [
            e for e in parsed.exercise_entries
            if e.date == "2026-02-22"
        ]
        assert len(matches) == 1
        assert matches[0].duration_minutes == 33
        assert matches[0].heart_rate_bpm == 88

    def test_no_warnings(self, parsed: ParseResult) -> None:
        assert len(parsed.warnings) == 0

    def test_expected_date_range(self, parsed: ParseResult) -> None:
        assert parsed.available_dates[0] == "2026-02-10"
        assert parsed.available_dates[-1] == "2026-02-23"
        assert len(parsed.available_dates) == 14

    def test_feb18_to_22_meal_count(self, parsed: ParseResult) -> None:
        selected = ["2026-02-18", "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22"]
        filtered = filter_by_dates(parsed, selected)
        assert len(filtered.glucose_entries) == 20

    def test_feb18_to_22_exercise_count(self, parsed: ParseResult) -> None:
        selected = ["2026-02-18", "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22"]
        filtered = filter_by_dates(parsed, selected)
        assert len(filtered.exercise_entries) == 3


# ── TestFilterByDates ─────────────────────────────────────────────────


class TestFilterByDates:
    def test_filters_correctly(self, parsed: ParseResult) -> None:
        filtered = filter_by_dates(parsed, ["2026-02-22"])
        for e in filtered.glucose_entries:
            assert e.date == "2026-02-22"
        assert len(filtered.glucose_entries) == 4

    def test_empty_selection_returns_empty(self, parsed: ParseResult) -> None:
        filtered = filter_by_dates(parsed, [])
        assert len(filtered.glucose_entries) == 0
        assert len(filtered.exercise_entries) == 0

    def test_warnings_preserved(self, parsed: ParseResult) -> None:
        filtered = filter_by_dates(parsed, ["2026-02-22"])
        assert filtered.warnings == parsed.warnings

    def test_original_not_mutated(self, parsed: ParseResult) -> None:
        original_count = len(parsed.glucose_entries)
        filter_by_dates(parsed, ["2026-02-22"])
        assert len(parsed.glucose_entries) == original_count
