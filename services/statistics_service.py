import sqlite3
from datetime import date

DB = "database/focusflow.db"


def get_statistics(filter_type="All"):
    
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()

    # Ensure sessions table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            completed_at TEXT,

            minutes INTEGER

        )
    """)

    # -----------------------
    # Sessions
    # -----------------------

    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(minutes),0) FROM sessions")
    total_minutes = cursor.fetchone()[0]

    today = date.today().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT IFNULL(SUM(minutes),0)

        FROM sessions

        WHERE completed_at LIKE ?
    """, (today + "%",))

    today_minutes = cursor.fetchone()[0]

    # -----------------------
    # Tasks
    # -----------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,

            category TEXT,

            priority TEXT,

            due_date TEXT,

            completed INTEGER DEFAULT 0,

            pomodoros INTEGER DEFAULT 0

        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)

        FROM tasks

        WHERE completed=1
    """)
    completed_tasks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)

        FROM tasks

        WHERE completed=0
    """)
    pending_tasks = cursor.fetchone()[0]

    if total_tasks == 0:
        completion_rate = 0
    else:
        completion_rate = round(
            completed_tasks / total_tasks * 100,
            1
        )

    connection.close()

    return {

        "sessions": total_sessions,

        "focus": total_minutes,

        "today": today_minutes,

        "completed": completed_tasks,

        "pending": pending_tasks,

        "completion": completion_rate

    }