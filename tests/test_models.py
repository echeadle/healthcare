from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import (
    ExerciseEntry,
    GlucoseEntry,
    MealType,
    MoodEntry,
    ReportSession,
    SessionStatus,
    TimeSlot,
)


class TestGlucoseEntry:
    def test_create_valid(self) -> None:
        entry = GlucoseEntry(
            date="2026-02-22",
            time="9:40 AM",
            glucose_reading=117,
            food_item="Egg omelette, salad, cottage cheese",
            meal_type=MealType.BREAKFAST,
        )
        assert entry.glucose_reading == 117
        assert entry.meal_type == MealType.BREAKFAST

    def test_all_meal_types(self) -> None:
        for meal_type in MealType:
            entry = GlucoseEntry(
                date="2026-02-22",
                time="9:40 AM",
                glucose_reading=100,
                food_item="Test food",
                meal_type=meal_type,
            )
            assert entry.meal_type == meal_type

    def test_rejects_negative_glucose(self) -> None:
        with pytest.raises(ValidationError, match="glucose_reading must be positive"):
            GlucoseEntry(
                date="2026-02-22",
                time="9:40 AM",
                glucose_reading=-5,
                food_item="Test",
                meal_type=MealType.BREAKFAST,
            )

    def test_rejects_zero_glucose(self) -> None:
        with pytest.raises(ValidationError, match="glucose_reading must be positive"):
            GlucoseEntry(
                date="2026-02-22",
                time="9:40 AM",
                glucose_reading=0,
                food_item="Test",
                meal_type=MealType.BREAKFAST,
            )

    def test_strips_whitespace(self) -> None:
        entry = GlucoseEntry(
            date="2026-02-22",
            time="9:40 AM",
            glucose_reading=100,
            food_item="  Oatmeal  ",
            meal_type=MealType.BREAKFAST,
        )
        assert entry.food_item == "Oatmeal"


class TestExerciseEntry:
    def test_create_valid(self) -> None:
        entry = ExerciseEntry(
            date="2026-02-22",
            time="10:56 AM",
            activity_type="Walking",
            duration_minutes=33,
            heart_rate_bpm=88,
            glucose_reading=108,
        )
        assert entry.activity_type == "Walking"
        assert entry.duration_minutes == 33
        assert entry.heart_rate_bpm == 88

    def test_rejects_negative_glucose(self) -> None:
        with pytest.raises(ValidationError):
            ExerciseEntry(
                date="2026-02-22",
                time="10:56 AM",
                activity_type="Walking",
                duration_minutes=33,
                heart_rate_bpm=88,
                glucose_reading=-1,
            )


class TestMoodEntry:
    def test_create_valid(self) -> None:
        entry = MoodEntry(
            date="2026-02-22",
            time_slot=TimeSlot.AFTER_BREAKING_FAST,
            time="9:40 AM",
            energy="Tired",
            mood=3,
        )
        assert entry.mood == 3
        assert entry.energy == "Tired"

    def test_all_time_slots(self) -> None:
        for slot in TimeSlot:
            entry = MoodEntry(
                date="2026-02-22",
                time_slot=slot,
                time="12:00 PM",
                energy="Ok",
                mood=3,
            )
            assert entry.time_slot == slot

    def test_rejects_mood_below_range(self) -> None:
        with pytest.raises(ValidationError, match="mood must be between 1 and 5"):
            MoodEntry(
                date="2026-02-22",
                time_slot=TimeSlot.AROUND_NOON,
                time="12:00 PM",
                energy="Ok",
                mood=0,
            )

    def test_rejects_mood_above_range(self) -> None:
        with pytest.raises(ValidationError, match="mood must be between 1 and 5"):
            MoodEntry(
                date="2026-02-22",
                time_slot=TimeSlot.AROUND_NOON,
                time="12:00 PM",
                energy="Ok",
                mood=6,
            )

    def test_mood_boundary_values(self) -> None:
        for mood_val in [1, 5]:
            entry = MoodEntry(
                date="2026-02-22",
                time_slot=TimeSlot.AROUND_NOON,
                time="12:00 PM",
                energy="Ok",
                mood=mood_val,
            )
            assert entry.mood == mood_val


class TestReportSession:
    def test_create_new_generates_id_and_timestamp(self) -> None:
        session = ReportSession.create_new(
            name="Test Session",
            date_range_start="2026-02-18",
            date_range_end="2026-02-22",
            selected_dates=["2026-02-18", "2026-02-19"],
        )
        assert len(session.id) > 0
        assert len(session.created_at) > 0
        assert session.name == "Test Session"

    def test_default_status_is_draft(self) -> None:
        session = ReportSession.create_new(
            name="Test",
            date_range_start="2026-02-18",
            date_range_end="2026-02-22",
            selected_dates=[],
        )
        assert session.status == SessionStatus.DRAFT

    def test_default_entries_are_empty(self) -> None:
        session = ReportSession.create_new(
            name="Test",
            date_range_start="2026-02-18",
            date_range_end="2026-02-22",
            selected_dates=[],
        )
        assert session.glucose_entries == []
        assert session.exercise_entries == []
        assert session.mood_entries == []

    def test_serialization_round_trip(self) -> None:
        session = ReportSession.create_new(
            name="Round Trip Test",
            date_range_start="2026-02-18",
            date_range_end="2026-02-22",
            selected_dates=["2026-02-18", "2026-02-19"],
        )
        json_str = session.model_dump_json()
        restored = ReportSession.model_validate_json(json_str)
        assert restored.id == session.id
        assert restored.name == session.name
        assert restored.selected_dates == session.selected_dates

    def test_with_entries_populated(self) -> None:
        session = ReportSession.create_new(
            name="Full Session",
            date_range_start="2026-02-22",
            date_range_end="2026-02-22",
            selected_dates=["2026-02-22"],
        )
        session.glucose_entries.append(
            GlucoseEntry(
                date="2026-02-22",
                time="9:40 AM",
                glucose_reading=117,
                food_item="Egg omelette",
                meal_type=MealType.BREAKFAST,
            )
        )
        session.exercise_entries.append(
            ExerciseEntry(
                date="2026-02-22",
                time="10:56 AM",
                activity_type="Walking",
                duration_minutes=33,
                heart_rate_bpm=88,
                glucose_reading=108,
            )
        )
        session.mood_entries.append(
            MoodEntry(
                date="2026-02-22",
                time_slot=TimeSlot.AFTER_BREAKING_FAST,
                time="9:40 AM",
                energy="Tired",
                mood=3,
            )
        )

        json_str = session.model_dump_json()
        restored = ReportSession.model_validate_json(json_str)
        assert len(restored.glucose_entries) == 1
        assert len(restored.exercise_entries) == 1
        assert len(restored.mood_entries) == 1
        assert restored.glucose_entries[0].food_item == "Egg omelette"
