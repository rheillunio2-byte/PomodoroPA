"""Finished sessions, newest first."""
from __future__ import annotations

from services import db
from services._ranges import start_date


def get_history(filter_type: str = "All Time", search: str = "",
                session_type: str = "All") -> list[tuple]:
    """Return ``(completed_at, minutes, session_type, task_title)`` rows.

    ``filter_type``: ``All Time`` / ``Today`` / ``This Week`` / ``This Month``.
    ``session_type``: ``All`` / ``Work`` / ``Breaks``.
    The old query compared against SQLite's UTC ``DATE('now')`` while sessions
    are stored in local time, so "Today" was wrong around midnight.
    """
    clauses, params = [], []
    since = start_date(filter_type)
    if since:
        clauses.append("substr(s.completed_at,1,10)>=?")
        params.append(since)
    if session_type == "Work":
        clauses.append("s.session_type='Work'")
    elif session_type == "Breaks":
        clauses.append("s.session_type!='Work'")
    if search.strip():
        clauses.append("(s.completed_at LIKE ? OR s.session_type LIKE ? OR IFNULL(t.title,'') LIKE ?)")
        params += [f"%{search.strip()}%"] * 3
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with db.connect() as conn:
        return conn.execute(
            f"""SELECT s.completed_at, s.minutes, s.session_type, t.title
                FROM sessions s LEFT JOIN tasks t ON t.id = s.task_id
                {where} ORDER BY s.id DESC""", params).fetchall()
