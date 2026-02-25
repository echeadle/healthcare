from __future__ import annotations

import json
from pathlib import Path

from src.models import ReportSession

DEFAULT_SESSIONS_DIR = Path("data/sessions")


def save_session(
    session: ReportSession, base_dir: Path = DEFAULT_SESSIONS_DIR
) -> Path:
    """Save a session to a JSON file. Returns the file path."""
    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / f"{session.id}.json"
    file_path.write_text(session.model_dump_json(indent=2))
    return file_path


def load_session(
    session_id: str, base_dir: Path = DEFAULT_SESSIONS_DIR
) -> ReportSession:
    """Load a session from a JSON file by ID.

    Raises FileNotFoundError if the session does not exist.
    """
    file_path = base_dir / f"{session_id}.json"
    content = file_path.read_text()
    return ReportSession.model_validate_json(content)


def list_sessions(base_dir: Path = DEFAULT_SESSIONS_DIR) -> list[dict[str, str]]:
    """List all sessions with summary info.

    Returns a list of dicts with keys: id, name, status,
    date_range_start, date_range_end, created_at.
    Sorted by created_at descending (newest first).
    """
    if not base_dir.exists():
        return []

    summaries: list[dict[str, str]] = []
    for file_path in base_dir.glob("*.json"):
        try:
            data = json.loads(file_path.read_text())
            summaries.append({
                "id": data["id"],
                "name": data["name"],
                "status": data["status"],
                "date_range_start": data["date_range_start"],
                "date_range_end": data["date_range_end"],
                "created_at": data["created_at"],
            })
        except (json.JSONDecodeError, KeyError):
            continue

    summaries.sort(key=lambda s: s["created_at"], reverse=True)
    return summaries


def delete_session(
    session_id: str, base_dir: Path = DEFAULT_SESSIONS_DIR
) -> bool:
    """Delete a session file. Returns True if deleted, False if not found."""
    file_path = base_dir / f"{session_id}.json"
    try:
        file_path.unlink()
        return True
    except FileNotFoundError:
        return False
