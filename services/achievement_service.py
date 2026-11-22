"""Badges, with progress towards the ones that are still locked."""
from __future__ import annotations

from services import db
from services.streak_service import streaks

# key, icon name (see ui/engine/icons.py), title, description, metric, target
_DEFINITIONS = (
    ("first",     "play",    "First Pomodoro",   "Finish your first focus session", "sessions", 1),
    ("ten",       "timer",   "Warming up",       "Finish 10 focus sessions",        "sessions", 10),
    ("fifty",     "medal",   "In the zone",      "Finish 50 focus sessions",        "sessions", 50),
    ("hundred",   "trophy",  "Centurion",        "Finish 100 focus sessions",       "sessions", 100),
    ("tasks10",   "check",   "Task tamer",       "Complete 10 tasks",               "tasks", 10),
    ("tasks50",   "star",    "Finisher",         "Complete 50 tasks",               "tasks", 50),
    ("streak3",   "flame",   "On a roll",        "Focus 3 days in a row",           "streak", 3),
    ("streak7",   "flame",   "Full week",        "Focus 7 days in a row",           "streak", 7),
    ("streak30",  "zap",     "Unbreakable",      "Focus 30 days in a row",          "streak", 30),
    ("tenhours",  "target",  "Ten hours deep",   "Log 10 hours of focus",           "minutes", 600),
)


def get_achievements() -> list[dict]:
    with db.connect() as conn:
        sessions, minutes = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(minutes),0) FROM sessions WHERE session_type='Work'").fetchone()
        tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]
    _, best = streaks()
    metrics = {"sessions": sessions, "minutes": minutes, "tasks": tasks, "streak": best}

    result = []
    for key, icon, title, description, metric, target in _DEFINITIONS:
        value = metrics[metric]
        result.append({
            "key": key, "icon": icon, "title": title, "description": description,
            "target": target, "progress": min(value, target), "unlocked": value >= target,
        })
    return result
