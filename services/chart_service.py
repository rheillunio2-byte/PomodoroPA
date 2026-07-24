import sqlite3

DB = "database/focusflow.db"


def weekly_productivity():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            completed_at TEXT,

            minutes INTEGER

        )
    """)

    cursor.execute("""

        SELECT
            substr(completed_at,1,10),
            COUNT(*)

        FROM sessions

        GROUP BY substr(completed_at,1,10)

        ORDER BY completed_at DESC

        LIMIT 7

    """)

    rows = cursor.fetchall()

    rows.reverse()

    conn.close()

    return rows

def task_categories():

    import sqlite3

    conn = sqlite3.connect(DB)

    cursor = conn.cursor()

    cursor.execute("""

        SELECT category, COUNT(*)

        FROM tasks

        GROUP BY category

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows

def monthly_productivity():

    import sqlite3

    conn = sqlite3.connect(DB)

    cursor = conn.cursor()

    cursor.execute("""

        SELECT
            substr(completed_at,1,7),
            COUNT(*)

        FROM sessions

        GROUP BY substr(completed_at,1,7)

        ORDER BY substr(completed_at,1,7)

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows