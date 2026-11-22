"""CSV export.  (The file dialog lives in the UI layer, not here.)"""
from __future__ import annotations

import csv

from services import db


def export_sessions_csv(path: str) -> int:
    """Write every session to *path*; returns the number of rows exported."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT completed_at, minutes, session_type FROM sessions ORDER BY completed_at").fetchall()
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Completed at", "Minutes", "Type"])
        writer.writerows(rows)
    return len(rows)


def export_tasks_csv(path: str) -> int:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT title, category, priority, due_date, completed, pomodoros FROM tasks ORDER BY id"
        ).fetchall()
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Title", "Category", "Priority", "Due date", "Completed", "Pomodoros"])
        writer.writerows(rows)
    return len(rows)
