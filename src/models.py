from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class MealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class TimeSlot(StrEnum):
    AFTER_BREAKING_FAST = "after_breaking_fast"
    AROUND_NOON = "around_noon"
    AFTER_DINNER = "after_dinner"
    BEFORE_BED = "before_bed"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"


class GlucoseEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    time: str
    glucose_reading: int
    food_item: str
    meal_type: MealType

    @field_validator("glucose_reading")
    @classmethod
    def glucose_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("glucose_reading must be positive")
        return v


class ExerciseEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    time: str
    activity_type: str
    duration_minutes: int
    heart_rate_bpm: int
    glucose_reading: int

    @field_validator("glucose_reading")
    @classmethod
    def glucose_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("glucose_reading must be positive")
        return v


class MoodEntry(BaseModel):
    date: str
    time_slot: TimeSlot
    time: str
    energy: str
    mood: int

    @field_validator("mood")
    @classmethod
    def mood_must_be_in_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("mood must be between 1 and 5")
        return v


class ReportSession(BaseModel):
    id: str
    name: str
    created_at: str
    date_range_start: str
    date_range_end: str
    selected_dates: list[str]
    glucose_entries: list[GlucoseEntry] = []
    exercise_entries: list[ExerciseEntry] = []
    mood_entries: list[MoodEntry] = []
    status: SessionStatus = SessionStatus.DRAFT
    source_filename: str = ""

    @classmethod
    def create_new(
        cls,
        name: str,
        date_range_start: str,
        date_range_end: str,
        selected_dates: list[str],
    ) -> ReportSession:
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            selected_dates=selected_dates,
        )
