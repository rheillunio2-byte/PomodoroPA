"""Single entry point to the SQLite database.

Before v2 every service opened ``database/focusflow.db`` relative to the
current working directory and several of them re-created the ``sessions``
table with *different* schemas.  All of that is now centralised here:

* ``connect()``  – context manager (commit on success, rollback on error)
* ``init_db()``  – creates every table and migrates older databases in place
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

import config

_SCHEMA = {
    "tasks": """
        CREATE TABLE IF NOT EXISTS tasks(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            category     TEXT,
            priority     TEXT,
            due_date     TEXT,
            completed    INTEGER DEFAULT 0,
            pomodoros    INTEGER DEFAULT 0
        )""",
    "sessions": """
        CREATE TABLE IF NOT EXISTS sessions(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            completed_at TEXT,
            minutes      INTEGER,
            session_type TEXT DEFAULT 'Work'
        )""",
    "settings": """
        CREATE TABLE IF NOT EXISTS settings(
            id               INTEGER PRIMARY KEY,
            work_minutes     INTEGER,
            short_break      INTEGER,
            long_break       INTEGER,
            long_break_every INTEGER,
            notifications    INTEGER DEFAULT 1,
            sounds           INTEGER DEFAULT 1
        )""",
}

# Columns added after v1.0.  (table -> {column: DDL fragment})
_MIGRATIONS = {
    "tasks": {
        "pomodoros": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "completed_at": "TEXT",
    },
    "sessions": {
        "session_type": "TEXT DEFAULT 'Work'",
        "task_id": "INTEGER",
    },
    "settings": {
        "notifications": "INTEGER DEFAULT 1",
        "sounds": "INTEGER DEFAULT 1",
        "theme": "TEXT DEFAULT 'Dark'",
        "auto_start": "INTEGER DEFAULT 1",
        "daily_goal": "INTEGER DEFAULT 4",
        "animations": "INTEGER DEFAULT 1",
        "cursor_fx": "INTEGER DEFAULT 1",
    },
}

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_sessions_completed ON sessions(completed_at)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)",
)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open the database; commit on success, roll back on error, always close."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def init_db() -> None:
    """Create missing tables / columns.  Safe to call any number of times."""
    with connect() as conn:
        for ddl in _SCHEMA.values():
            conn.execute(ddl)

        for table, columns in _MIGRATIONS.items():
            have = _existing_columns(conn, table)
            for column, ddl in columns.items():
                if column not in have:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

        # v1 stored the user's settings in a single row with id = 1.
        conn.execute(
            """INSERT OR IGNORE INTO settings
               (id, work_minutes, short_break, long_break, long_break_every,
                notifications, sounds)
               VALUES (1, 25, 5, 15, 4, 1, 1)"""
        )
        # Rows created by an older version get sensible values for new columns.
        conn.execute("UPDATE settings SET theme='Dark' WHERE theme IS NULL")
        for column, default in (("auto_start", 1), ("daily_goal", 4),
                                ("animations", 1), ("cursor_fx", 1)):
            conn.execute(f"UPDATE settings SET {column}=? WHERE {column} IS NULL", (default,))
        conn.execute("UPDATE sessions SET session_type='Work' WHERE session_type IS NULL")

        for statement in _INDEXES:
            conn.execute(statement)
