"""Create, read, update and delete tasks."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import config
from services import db

MAX_TITLE_LENGTH = 120

# Sorting urgent work first.  Done in SQL so the UI never has to re-sort.
_PRIORITY_RANK = """CASE priority
    WHEN 'Urgent' THEN 4 WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 ELSE 0 END"""

_COLUMNS = "id, title, category, priority, due_date, completed, pomodoros"


def initialize_tasks() -> None:
    """Kept for backwards compatibility – the schema is created in db.init_db()."""
    db.init_db()


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------

def parse_due_date(text: str | None, today: date | None = None) -> str:
    """Turn user input into ``YYYY-MM-DD`` (or ``''`` for "no due date").

    Accepts ISO dates (``2026-07-31``, ``2026/07/31``) and the words
    ``today`` / ``tomorrow``.  Raises ``ValueError`` for anything else, so the
    UI can show a useful message instead of silently saving garbage (which
    used to crash the calendar page later on).
    """
    value = (text or "").strip().lower()
    if not value:
        return ""
    today = today or date.today()
    if value == "today":
        return today.isoformat()
    if value == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    try:
        return datetime.strptime(value.replace("/", "-"), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Use the format YYYY-MM-DD, or type 'today' or 'tomorrow'.") from None


def _validate(title: str, category: str, priority: str, due_date: str | None) -> tuple[str, str, str, str]:
    title = (title or "").strip()
    if not title:
        raise ValueError("Give the task a title.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Keep the title under {MAX_TITLE_LENGTH} characters.")
    if category not in config.CATEGORIES:
        raise ValueError("Pick one of the available categories.")
    if priority not in config.PRIORITIES:
        raise ValueError("Pick one of the available priorities.")
    return title, category, priority, parse_due_date(due_date)


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------

def add_task(title, category, priority, due_date="") -> int:
    title, category, priority, due = _validate(title, category, priority, due_date)
    with db.connect() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, category, priority, due_date, created_at) VALUES (?,?,?,?,?)",
            (title, category, priority, due, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return cursor.lastrowid


def get_tasks(search: str = "", category: str = "All", priority: str = "All",
              status: str = "All") -> list[tuple]:
    """Return ``(id, title, category, priority, due_date, completed, pomodoros)`` rows.

    ``status`` is ``All`` / ``Active`` / ``Done``.  Open tasks come first,
    ordered by priority and then by due date (undated tasks last).
    """
    clauses, params = [], []
    if search.strip():
        clauses.append("title LIKE ? ESCAPE '\\'")
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.append(f"%{escaped}%")
    if category not in ("", "All"):
        clauses.append("category=?")
        params.append(category)
    if priority not in ("", "All"):
        clauses.append("priority=?")
        params.append(priority)
    if status == "Active":
        clauses.append("completed=0")
    elif status == "Done":
        clauses.append("completed=1")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT {_COLUMNS} FROM tasks {where}
        ORDER BY completed ASC,
                 {_PRIORITY_RANK} DESC,
                 CASE WHEN due_date IS NULL OR due_date='' THEN 1 ELSE 0 END,
                 due_date ASC,
                 id DESC"""
    with db.connect() as conn:
        return conn.execute(query, params).fetchall()


def get_task(task_id: int):
    with db.connect() as conn:
        return conn.execute(f"SELECT {_COLUMNS} FROM tasks WHERE id=?", (task_id,)).fetchone()


def update_task(task_id, title, category, priority, due_date="") -> None:
    title, category, priority, due = _validate(title, category, priority, due_date)
    with db.connect() as conn:
        conn.execute(
            "UPDATE tasks SET title=?, category=?, priority=?, due_date=? WHERE id=?",
            (title, category, priority, due, task_id),
        )


def complete_task(task_id: int) -> None:
    with db.connect() as conn:
        conn.execute(
            "UPDATE tasks SET completed=1, completed_at=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id),
        )


def reopen_task(task_id: int) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE tasks SET completed=0, completed_at=NULL WHERE id=?", (task_id,))


def delete_task(task_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.execute("UPDATE sessions SET task_id=NULL WHERE task_id=?", (task_id,))


def add_pomodoro(task_id: int) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE tasks SET pomodoros = IFNULL(pomodoros,0) + 1 WHERE id=?", (task_id,))


def count_pending() -> int:
    with db.connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=0").fetchone()[0]
