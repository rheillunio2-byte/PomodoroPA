import sqlite3
from datetime import datetime

DB = "database/focusflow.db"

def save_session(minutes, session_type):

    connection = sqlite3.connect(DB)

    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        completed_at TEXT,

        minutes INTEGER,

        session_type TEXT DEFAULT 'Work'

    )
    """)

    cursor.execute("""
    INSERT INTO sessions
    (
        completed_at,
        minutes,
        session_type
    )
    VALUES (?,?,?)
    """,(

        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        minutes,

        session_type

    ))

    connection.commit()

    connection.close()