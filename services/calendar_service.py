import sqlite3
from datetime import date

DB = "database/focusflow.db"


def get_tasks_by_date(date):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            category,
            priority,
            completed
        FROM tasks
        WHERE due_date=?
        ORDER BY priority DESC
    """, (date,))

    rows = cursor.fetchall()

    conn.close()

    return rows

def get_task_dates():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT due_date
        FROM tasks
        WHERE due_date IS NOT NULL
          AND due_date != ''
    """)

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]

def get_upcoming_tasks(limit=5):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    today = date.today().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT
            title,
            due_date,
            priority
        FROM tasks
        WHERE completed=0
          AND due_date>=?
        ORDER BY due_date ASC
        LIMIT ?
    """, (today, limit))

    rows = cursor.fetchall()

    conn.close()

    return rows