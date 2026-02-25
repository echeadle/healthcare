from __future__ import annotations

from pathlib import Path

import pytest

from src.models import (
    GlucoseEntry,
    MealType,
    MoodEntry,
    ReportSession,
    TimeSlot,
)
from src.storage import delete_session, list_sessions, load_session, save_session


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    """Provide an isolated temporary directory for session storage."""
    return tmp_path / "sessions"


def _make_session(name: str = "Test Session") -> ReportSession:
    return ReportSession.create_new(
        name=name,
        date_range_start="2026-02-18",
        date_range_end="2026-02-22",
        selected_dates=["2026-02-18", "2026-02-19"],
    )


class TestSaveSession:
    def test_creates_json_file(self, sessions_dir: Path) -> None:
        session = _make_session()
        path = save_session(session, base_dir=sessions_dir)
        assert path.exists()
        assert path.suffix == ".json"

    def test_file_contains_valid_json(self, sessions_dir: Path) -> None:
        session = _make_session()
        path = save_session(session, base_dir=sessions_dir)
        loaded = ReportSession.model_validate_json(path.read_text())
        assert loaded.id == session.id


class TestLoadSession:
    def test_returns_correct_data(self, sessions_dir: Path) -> None:
        session = _make_session("Load Test")
        save_session(session, base_dir=sessions_dir)
        loaded = load_session(session.id, base_dir=sessions_dir)
        assert loaded.name == "Load Test"
        assert loaded.id == session.id

    def test_nonexistent_id_raises(self, sessions_dir: Path) -> None:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        with pytest.raises(FileNotFoundError):
            load_session("nonexistent-id", base_dir=sessions_dir)


class TestListSessions:
    def test_returns_summaries(self, sessions_dir: Path) -> None:
        save_session(_make_session("Session A"), base_dir=sessions_dir)
        save_session(_make_session("Session B"), base_dir=sessions_dir)
        summaries = list_sessions(base_dir=sessions_dir)
        assert len(summaries) == 2
        names = {s["name"] for s in summaries}
        assert "Session A" in names
        assert "Session B" in names

    def test_empty_directory_returns_empty_list(self, sessions_dir: Path) -> None:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        assert list_sessions(base_dir=sessions_dir) == []

    def test_nonexistent_directory_returns_empty_list(
        self, sessions_dir: Path
    ) -> None:
        assert list_sessions(base_dir=sessions_dir) == []

    def test_summaries_have_expected_keys(self, sessions_dir: Path) -> None:
        save_session(_make_session(), base_dir=sessions_dir)
        summaries = list_sessions(base_dir=sessions_dir)
        expected_keys = {
            "id",
            "name",
            "status",
            "date_range_start",
            "date_range_end",
            "created_at",
        }
        assert set(summaries[0].keys()) == expected_keys


class TestDeleteSession:
    def test_removes_file(self, sessions_dir: Path) -> None:
        session = _make_session()
        save_session(session, base_dir=sessions_dir)
        result = delete_session(session.id, base_dir=sessions_dir)
        assert result is True
        assert not (sessions_dir / f"{session.id}.json").exists()

    def test_nonexistent_id_returns_false(self, sessions_dir: Path) -> None:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        result = delete_session("nonexistent-id", base_dir=sessions_dir)
        assert result is False


class TestRoundTrip:
    def test_preserves_all_data_with_entries(self, sessions_dir: Path) -> None:
        session = _make_session("Full Round Trip")
        session.glucose_entries.append(
            GlucoseEntry(
                date="2026-02-22",
                time="9:40 AM",
                glucose_reading=117,
                food_item="Egg omelette",
                meal_type=MealType.BREAKFAST,
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

        save_session(session, base_dir=sessions_dir)
        loaded = load_session(session.id, base_dir=sessions_dir)

        assert loaded.name == "Full Round Trip"
        assert len(loaded.glucose_entries) == 1
        assert loaded.glucose_entries[0].food_item == "Egg omelette"
        assert len(loaded.mood_entries) == 1
        assert loaded.mood_entries[0].energy == "Tired"
