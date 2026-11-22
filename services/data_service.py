"""Data-management helpers used by the Settings page."""
from __future__ import annotations

import config
from services import db


def reset_all_data() -> None:
    """Delete every task and session (settings are kept)."""
    with db.connect() as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('tasks','sessions')")


def data_folder() -> str:
    return str(config.DB_PATH.parent)
