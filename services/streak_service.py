"""Consecutive-day streaks of focused work."""
from __future__ import annotations

from datetime import date, timedelta

from services import db


def _work_days() -> list[date]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(completed_at,1,10) FROM sessions "
            "WHERE session_type='Work' AND completed_at IS NOT NULL ORDER BY 1 DESC").fetchall()
    days = []
    for (text,) in rows:
        try:
            days.append(date.fromisoformat(text))
        except (TypeError, ValueError):
            continue
    return days


def streaks(today: date | None = None) -> tuple[int, int]:
    """Return ``(current, best)`` streak lengths in days.

    The current streak stays alive until the end of *tomorrow*'s first
    session, i.e. having worked yesterday but not yet today still counts.
    """
    today = today or date.today()
    days = _work_days()
    if not days:
        return 0, 0

    current = 0
    expected = today if days[0] == today else today - timedelta(days=1)
    if days[0] in (today, today - timedelta(days=1)):
        for day in days:
            if day == expected:
                current += 1
                expected -= timedelta(days=1)
            elif day < expected:
                break

    best = run = 1
    for newer, older in zip(days, days[1:]):
        run = run + 1 if (newer - older).days == 1 else 1
        best = max(best, run)
    return current, max(best, current)


def get_current_streak() -> int:
    return streaks()[0]
