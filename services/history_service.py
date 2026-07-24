import sqlite3

DB = "database/focusflow.db"

def get_history(filter_type="All Time"):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        completed_at TEXT,

        minutes INTEGER,

        session_type TEXT DEFAULT 'Work'

    )
    """)

    cursor.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cursor.fetchall()]

    if "session_type" not in columns:
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN session_type TEXT DEFAULT 'Work'
        """)
        conn.commit()

    from datetime import datetime, timedelta

    today = datetime.today()

    if filter_type == "Today":

        cursor.execute("""
            SELECT completed_at, minutes, session_type
            FROM sessions
            WHERE DATE(completed_at)=DATE('now')
            ORDER BY id DESC
        """)

    elif filter_type == "This Week":

        week = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT completed_at, minutes, session_type
            FROM sessions
            WHERE completed_at>=?
            ORDER BY id DESC
        """, (week,))

    elif filter_type == "This Month":

        month = today.strftime("%Y-%m")

        cursor.execute("""
            SELECT completed_at, minutes, session_type
            FROM sessions
            WHERE completed_at LIKE ?
            ORDER BY id DESC
        """, (month + "%",))

    else:

        cursor.execute("""
            SELECT completed_at, minutes, session_type
            FROM sessions
            ORDER BY id DESC
        """)

    rows = cursor.fetchall()

    conn.close()

    return rows