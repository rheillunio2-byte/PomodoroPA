"""Numbers for the Dashboard."""
from __future__ import annotations

from datetime import date

from services import db
from services.settings_service import get_settings
from services.streak_service import streaks


def get_dashboard_stats() -> dict:
    today = date.today().isoformat()
    with db.connect() as conn:
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=0").fetchone()[0]
        pomodoros, minutes = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(minutes),0) FROM sessions WHERE session_type='Work'"
        ).fetchone()
        today_count, today_minutes = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(minutes),0) FROM sessions "
            "WHERE session_type='Work' AND substr(completed_at,1,10)=?", (today,)
        ).fetchone()
        overdue = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE completed=0 AND due_date!='' AND due_date<?",
            (today,)).fetchone()[0]

    current, best = streaks()
    return {
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "pomodoros": pomodoros,
        # v1 multiplied the pomodoro count by 25 regardless of the user's
        # settings; now it is the real sum of finished work minutes.
        "focus_minutes": minutes,
        "today_pomodoros": today_count,
        "today_minutes": today_minutes,
        "daily_goal": get_settings()["daily_goal"],
        "streak": current,
        "best_streak": best,
    }
