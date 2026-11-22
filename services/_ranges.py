"""Date-range helpers shared by the statistics, chart and history services."""
from __future__ import annotations

from datetime import date, timedelta

# Number of days *before today* that each named range reaches back.
_SPAN = {"Today": 0, "Week": 6, "This Week": 6, "Month": 29, "This Month": 29}


def start_date(range_name: str, today: date | None = None) -> str | None:
    """First day (``YYYY-MM-DD``) covered by *range_name*; ``None`` means "everything"."""
    span = _SPAN.get(range_name)
    if span is None:
        return None
    return ((today or date.today()) - timedelta(days=span)).isoformat()
