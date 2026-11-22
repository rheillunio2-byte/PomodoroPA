"""Aggregations that feed the charts."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from services import db

_WORK = "session_type='Work'"


def _minutes_by_day(conn, since: str) -> dict[str, tuple[int, int]]:
    rows = conn.execute(
        f"""SELECT substr(completed_at,1,10) AS d, IFNULL(SUM(minutes),0), COUNT(*)
            FROM sessions WHERE {_WORK} AND substr(completed_at,1,10)>=?
            GROUP BY d""", (since,)).fetchall()
    return {d: (m, c) for d, m, c in rows}


def daily_focus(days: int = 7) -> list[tuple[str, int, int]]:
    """``(YYYY-MM-DD, focus_minutes, sessions)`` for each of the last *days* days.

    Days without sessions are included as zeros so charts always show a
    continuous axis (v1 only returned days that had data).
    """
    today = date.today()
    first = today - timedelta(days=days - 1)
    with db.connect() as conn:
        data = _minutes_by_day(conn, first.isoformat())
    out = []
    for offset in range(days):
        day = (first + timedelta(days=offset)).isoformat()
        minutes, count = data.get(day, (0, 0))
        out.append((day, minutes, count))
    return out


def weekly_productivity() -> list[tuple[str, int]]:
    """v1-compatible: ``(date, sessions)`` for the last seven days."""
    return [(d, c) for d, _, c in daily_focus(7)]


def hourly_focus(day: date | None = None) -> list[tuple[str, int]]:
    day = (day or date.today()).isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            f"""SELECT CAST(substr(completed_at,12,2) AS INTEGER), IFNULL(SUM(minutes),0)
                FROM sessions WHERE {_WORK} AND substr(completed_at,1,10)=? GROUP BY 1""",
            (day,)).fetchall()
    by_hour = dict(rows)
    return [(f"{h:02d}", by_hour.get(h, 0)) for h in range(24)]


def monthly_focus(months: int = 12) -> list[tuple[str, int]]:
    """``(YYYY-MM, focus_minutes)`` for the last *months* calendar months."""
    today = date.today()
    keys = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    keys.reverse()
    with db.connect() as conn:
        rows = conn.execute(
            f"""SELECT substr(completed_at,1,7), IFNULL(SUM(minutes),0)
                FROM sessions WHERE {_WORK} AND substr(completed_at,1,7)>=? GROUP BY 1""",
            (keys[0],)).fetchall()
    data = dict(rows)
    return [(k, data.get(k, 0)) for k in keys]


def monthly_productivity() -> list[tuple[str, int]]:
    """v1-compatible: ``(YYYY-MM, sessions)`` for months that have data."""
    with db.connect() as conn:
        return conn.execute(
            f"""SELECT substr(completed_at,1,7), COUNT(*) FROM sessions
                WHERE {_WORK} GROUP BY 1 ORDER BY 1""").fetchall()


def focus_series(range_name: str) -> tuple[str, list[tuple[str, int]]]:
    """Title and ``(label, minutes)`` bars that suit the chosen range."""
    if range_name == "Today":
        return "Focus minutes by hour", hourly_focus()
    if range_name == "Week":
        rows = daily_focus(7)
        return "Focus minutes per day", [(datetime.strptime(d, "%Y-%m-%d").strftime("%a"), m) for d, m, _ in rows]
    if range_name == "Month":
        rows = daily_focus(30)
        return "Focus minutes per day", [(datetime.strptime(d, "%Y-%m-%d").strftime("%d"), m) for d, m, _ in rows]
    rows = monthly_focus(12)
    return "Focus minutes per month", [(datetime.strptime(k, "%Y-%m").strftime("%b"), m) for k, m in rows]


def task_categories() -> list[tuple[str, int]]:
    with db.connect() as conn:
        return conn.execute(
            """SELECT IFNULL(NULLIF(category,''),'Other'), COUNT(*) FROM tasks
               GROUP BY 1 ORDER BY 2 DESC""").fetchall()


def activity_heatmap(weeks: int = 12) -> tuple[date, dict[str, int]]:
    """Focus minutes per day for a GitHub-style grid.

    Returns the Monday that starts the grid and a ``{YYYY-MM-DD: minutes}`` map.
    """
    today = date.today()
    start = today - timedelta(days=today.weekday() + 7 * (weeks - 1))
    with db.connect() as conn:
        data = _minutes_by_day(conn, start.isoformat())
    return start, {d: m for d, (m, _) in data.items()}
