import sqlite3

DB = "database/focusflow.db"


def initialize_settings():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings(

        id INTEGER PRIMARY KEY,

        work_minutes INTEGER,

        short_break INTEGER,

        long_break INTEGER,

        long_break_every INTEGER,

        notifications INTEGER DEFAULT 1,

        sounds INTEGER DEFAULT 1

    )
    """)

    # Upgrade older databases
    cursor.execute("PRAGMA table_info(settings)")
    columns = [row[1] for row in cursor.fetchall()]

    if "notifications" not in columns:
        cursor.execute("""
            ALTER TABLE settings
            ADD COLUMN notifications INTEGER DEFAULT 1
        """)

    if "sounds" not in columns:
        cursor.execute("""
            ALTER TABLE settings
            ADD COLUMN sounds INTEGER DEFAULT 1
        """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings
    (
        id,
        work_minutes,
        short_break,
        long_break,
        long_break_every,
        notifications,
        sounds
    )
    VALUES
    (
        1,
        25,
        5,
        15,
        4,
        1,
        1
    )
    """)

    conn.commit()
    conn.close()


def save_settings(work, short, long_break, interval):

    initialize_settings()

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE settings
    SET

        work_minutes=?,

        short_break=?,

        long_break=?,

        long_break_every=?

    WHERE id=1
    """, (

        work,
        short,
        long_break,
        interval

    ))

    conn.commit()
    conn.close()


def load_settings():

    initialize_settings()

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT

        work_minutes,

        short_break,

        long_break,

        long_break_every

    FROM settings

    WHERE id=1
    """)

    row = cursor.fetchone()

    conn.close()

    return row


def save_notification_settings(notifications, sounds):

    initialize_settings()

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE settings

    SET

        notifications=?,

        sounds=?

    WHERE id=1
    """, (

        notifications,
        sounds

    ))

    conn.commit()
    conn.close()


def load_notification_settings():

    initialize_settings()

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT

        notifications,

        sounds

    FROM settings

    WHERE id=1
    """)

    row = cursor.fetchone()

    conn.close()

    return row