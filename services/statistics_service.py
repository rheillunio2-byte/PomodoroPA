"""Headline numbers for the Statistics page."""
from __future__ import annotations

from datetime import date

from services import db
from services._ranges import start_date


def get_statistics(filter_type: str = "All") -> dict:
    """Summary figures for a range (``Today`` / ``Week`` / ``Month`` / ``All``).

    v1 accepted a filter but ignored it.  Session figures now honour the
    range, and only *work* sessions count as focus time (breaks used to be
    indistinguishable from focus).
    """
    since = start_date(filter_type)
    today = date.today().isoformat()
    session_where = "session_type='Work'" + (" AND substr(completed_at,1,10)>=?" if since else "")
    params = (since,) if since else ()

    with db.connect() as conn:
        sessions, minutes = conn.execute(
            f"SELECT COUNT(*), IFNULL(SUM(minutes),0) FROM sessions WHERE {session_where}", params
        ).fetchone()
        today_minutes = conn.execute(
            "SELECT IFNULL(SUM(minutes),0) FROM sessions "
            "WHERE session_type='Work' AND substr(completed_at,1,10)=?", (today,)
        ).fetchone()[0]

        task_where = "completed=1" + (
            " AND substr(IFNULL(completed_at,''),1,10)>=?" if since else "")
        completed = conn.execute(f"SELECT COUNT(*) FROM tasks WHERE {task_where}", params).fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=0").fetchone()[0]
        done_total = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]

    total = done_total + pending
    return {
        "sessions": sessions,
        "focus": minutes,
        "today": today_minutes,
        "completed": completed,
        "pending": pending,
        "completion": round(done_total / total * 100, 1) if total else 0,
        "avg_session": round(minutes / sessions) if sessions else 0,
    }
