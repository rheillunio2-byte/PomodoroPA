"""Plain-language observations about the user's focus habits.

These are simple, transparent rules over the user's own history (nothing is
sent anywhere).  The Statistics page presents them as "Insights".
"""
from __future__ import annotations

from services import db

_WEEKDAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


def get_insights() -> dict:
    """Return ``{"metrics": [(icon, label, value)], "tips": [str]}``."""
    with db.connect() as conn:
        total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]
        sessions, minutes, active_days = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(minutes),0), COUNT(DISTINCT substr(completed_at,1,10)) "
            "FROM sessions WHERE session_type='Work'").fetchone()
        category = conn.execute(
            """SELECT IFNULL(NULLIF(category,''),'Other'), COUNT(*) FROM tasks
               GROUP BY 1 ORDER BY 2 DESC LIMIT 1""").fetchone()
        weekday = conn.execute(
            """SELECT CAST(strftime('%w', completed_at) AS INTEGER), SUM(minutes) FROM sessions
               WHERE session_type='Work' GROUP BY 1 ORDER BY 2 DESC LIMIT 1""").fetchone()

    completion = round(done_tasks / total_tasks * 100) if total_tasks else 0
    average = round(minutes / active_days) if active_days else 0

    metrics = [
        ("check", "Task completion", f"{completion}%"),
        ("timer", "Focus sessions", str(sessions)),
        ("clock", "Total focus time", _format_minutes(minutes)),
        ("target", "Average per active day", f"{average} min"),
    ]
    if category:
        metrics.append(("layers", "Most used category", category[0]))
    if weekday and weekday[1]:
        metrics.append(("flame", "Most productive day", _WEEKDAYS[weekday[0]]))

    tips = []
    if sessions == 0:
        tips.append("Start your first Pomodoro on the timer page – insights appear after a few sessions.")
    else:
        if total_tasks and completion < 50:
            tips.append("Finish a couple of small tasks first to build momentum.")
        elif total_tasks and completion < 80:
            tips.append("You are close to consistent: aim for an 80% completion rate.")
        elif total_tasks:
            tips.append("Excellent task completion – keep your current routine.")
        if average < 60:
            tips.append("Try for 60 focused minutes on each active day.")
        elif average < 120:
            tips.append("Stretch to 120 focused minutes a day for a deeper habit.")
        else:
            tips.append("Strong focus habit. Keep taking your breaks so it stays sustainable.")
        if sessions < 20:
            tips.append("A few more sessions will make these insights more reliable.")
        elif sessions > 100:
            tips.append("With 100+ sessions logged, consider raising your daily goal.")
    return {"metrics": metrics, "tips": tips}


def _format_minutes(total: int) -> str:
    hours, minutes = divmod(int(total), 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes} min"
