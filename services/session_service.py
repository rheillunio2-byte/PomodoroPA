"""Persist finished Pomodoro sessions."""
from __future__ import annotations

from datetime import datetime

from services import db

WORK, SHORT_BREAK, LONG_BREAK = "Work", "Short Break", "Long Break"


def save_session(minutes: int, session_type: str = WORK, task_id: int | None = None,
                 when: datetime | None = None) -> None:
    when = when or datetime.now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO sessions (completed_at, minutes, session_type, task_id) VALUES (?,?,?,?)",
            (when.strftime("%Y-%m-%d %H:%M:%S"), int(minutes), session_type, task_id),
        )


def work_sessions_today() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with db.connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE session_type='Work' AND substr(completed_at,1,10)=?",
            (today,),
        ).fetchone()[0]
