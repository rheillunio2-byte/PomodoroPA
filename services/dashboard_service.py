import sqlite3
from pathlib import Path

DB_PATH = Path("database/focusflow.db")


def get_dashboard_stats():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE completed=1
    """)
    completed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE completed=0
    """)
    pending = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(pomodoros),0)
        FROM tasks
    """)
    pomodoros = cursor.fetchone()[0]

    conn.close()

    return {

        "completed": completed,

        "pending": pending,

        "pomodoros": pomodoros,

        "focus_minutes": pomodoros * 25

    }