"""User preferences, stored in the single ``settings`` row (id = 1)."""
from __future__ import annotations

from typing import Any

from services import db

# key -> (default, minimum, maximum) for numbers, or (default, allowed values)
_NUMERIC = {
    "work_minutes": (25, 1, 180),
    "short_break": (5, 1, 60),
    "long_break": (15, 1, 120),
    "long_break_every": (4, 1, 30),
    "daily_goal": (4, 1, 24),
}
_FLAGS = ("notifications", "sounds", "auto_start", "animations", "cursor_fx")
THEMES = ("Dark", "Light", "System")

DEFAULTS: dict[str, Any] = {
    **{key: spec[0] for key, spec in _NUMERIC.items()},
    **{key: 1 for key in _FLAGS},
    "theme": "Dark",
}


def initialize_settings() -> None:
    db.init_db()


def _clean(key: str, value: Any) -> Any:
    """Validate one preference; raises ``ValueError`` with a readable message."""
    if key in _NUMERIC:
        _, low, high = _NUMERIC[key]
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a whole number.") from None
        if not low <= number <= high:
            raise ValueError(
                f"{key.replace('_', ' ').capitalize()} must be between {low} and {high}."
            )
        return number
    if key in _FLAGS:
        return 1 if value else 0
    if key == "theme":
        if value not in THEMES:
            raise ValueError(f"Theme must be one of: {', '.join(THEMES)}.")
        return value
    raise KeyError(f"Unknown setting: {key}")


def get_settings() -> dict[str, Any]:
    """Return every preference as a dict (missing values fall back to defaults)."""
    db.init_db()
    columns = list(DEFAULTS)
    with db.connect() as conn:
        row = conn.execute(f"SELECT {', '.join(columns)} FROM settings WHERE id=1").fetchone()
    values = dict(zip(columns, row)) if row else {}
    return {key: (DEFAULTS[key] if values.get(key) is None else values[key]) for key in columns}


def update_settings(**changes: Any) -> dict[str, Any]:
    """Validate and persist one or more preferences, returning the new state."""
    cleaned = {key: _clean(key, value) for key, value in changes.items()}
    if cleaned:
        db.init_db()
        assignments = ", ".join(f"{key}=?" for key in cleaned)
        with db.connect() as conn:
            conn.execute(f"UPDATE settings SET {assignments} WHERE id=1", tuple(cleaned.values()))
    return get_settings()


# ---------------------------------------------------------------------------
# v1-compatible helpers (kept so older code and forks keep working)
# ---------------------------------------------------------------------------

def load_settings() -> tuple[int, int, int, int]:
    s = get_settings()
    return s["work_minutes"], s["short_break"], s["long_break"], s["long_break_every"]


def save_settings(work, short, long_break, interval) -> None:
    update_settings(work_minutes=work, short_break=short,
                    long_break=long_break, long_break_every=interval)


def load_notification_settings() -> tuple[int, int]:
    s = get_settings()
    return s["notifications"], s["sounds"]


def save_notification_settings(notifications, sounds) -> None:
    update_settings(notifications=notifications, sounds=sounds)
