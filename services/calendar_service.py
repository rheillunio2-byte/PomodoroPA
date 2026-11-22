"""Task queries for the calendar."""
from __future__ import annotations

from datetime import date

from services import db

_RANK = """CASE priority WHEN 'Urgent' THEN 4 WHEN 'High' THEN 3 WHEN 'Medium' THEN 2
           WHEN 'Low' THEN 1 ELSE 0 END"""


def get_tasks_by_date(day: str) -> list[tuple]:
    """``(id, title, category, priority, completed)`` for one ``YYYY-MM-DD`` day."""
    with db.connect() as conn:
        return conn.execute(
            f"""SELECT id, title, category, priority, completed FROM tasks
                WHERE due_date=? ORDER BY completed ASC, {_RANK} DESC, id DESC""", (day,)).fetchall()


def get_task_dates() -> list[str]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT due_date FROM tasks WHERE due_date IS NOT NULL AND due_date!=''").fetchall()
    return [r[0] for r in rows]


def get_month_summary(year: int, month: int) -> dict[str, dict]:
    """Per-day task counts for one month, used to draw the dots on the grid.

    ``{"2026-07-24": {"total": 3, "done": 1, "rank": 4}}`` where ``rank`` is the
    highest priority among the day's *open* tasks (0 when all are done).
    """
    prefix = f"{year:04d}-{month:02d}-"
    with db.connect() as conn:
        rows = conn.execute(
            f"""SELECT due_date, COUNT(*), SUM(completed),
                       IFNULL(MAX(CASE WHEN completed=0 THEN {_RANK} END), 0)
                FROM tasks WHERE due_date LIKE ? GROUP BY due_date""", (prefix + "%",)).fetchall()
    return {d: {"total": t, "done": done or 0, "rank": rank} for d, t, done, rank in rows}


def get_upcoming_tasks(limit: int = 5) -> list[tuple]:
    """Open tasks due today or later: ``(title, due_date, priority)``."""
    today = date.today().isoformat()
    with db.connect() as conn:
        return conn.execute(
            """SELECT title, due_date, priority FROM tasks
               WHERE completed=0 AND due_date!='' AND due_date>=?
               ORDER BY due_date ASC LIMIT ?""", (today, limit)).fetchall()


def get_overdue_tasks(limit: int = 5) -> list[tuple]:
    today = date.today().isoformat()
    with db.connect() as conn:
        return conn.execute(
            """SELECT title, due_date, priority FROM tasks
               WHERE completed=0 AND due_date!='' AND due_date<?
               ORDER BY due_date DESC LIMIT ?""", (today, limit)).fetchall()
