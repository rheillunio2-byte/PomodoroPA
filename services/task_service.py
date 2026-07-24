import sqlite3
from pathlib import Path

DB_PATH = Path("database/focusflow.db")


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_tasks():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            category TEXT,

            priority TEXT,

            due_date TEXT,

            completed INTEGER DEFAULT 0,

            pomodoros INTEGER DEFAULT 0
        )
    """)

    connection.commit()

    # ------------------------------------------------------
    # Add pomodoros column automatically if upgrading
    # ------------------------------------------------------

    cursor.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cursor.fetchall()]

    if "pomodoros" not in columns:
        cursor.execute("""
            ALTER TABLE tasks
            ADD COLUMN pomodoros INTEGER DEFAULT 0
        """)
        connection.commit()

    connection.close()


# ==========================================================
# CREATE
# ==========================================================

def add_task(title, category, priority, due_date):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        INSERT INTO tasks
        (
            title,
            category,
            priority,
            due_date
        )

        VALUES
        (
            ?,?,?,?
        )

    """, (

        title,
        category,
        priority,
        due_date

    ))

    connection.commit()
    connection.close()


# ==========================================================
# READ
# ==========================================================

def get_tasks():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        SELECT
            id,
            title,
            category,
            priority,
            due_date,
            completed,
            pomodoros

        FROM tasks

        ORDER BY completed ASC,
                 id DESC

    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================================
# COMPLETE
# ==========================================================

def complete_task(task_id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        UPDATE tasks

        SET completed = 1

        WHERE id = ?

    """, (task_id,))

    connection.commit()
    connection.close()


# ==========================================================
# DELETE
# ==========================================================

def delete_task(task_id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        DELETE FROM tasks

        WHERE id = ?

    """, (task_id,))

    connection.commit()
    connection.close()


# ==========================================================
# UPDATE
# ==========================================================

def update_task(task_id, title, category, priority, due_date):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        UPDATE tasks

        SET
            title=?,
            category=?,
            priority=?,
            due_date=?

        WHERE id=?

    """, (

        title,
        category,
        priority,
        due_date,
        task_id

    ))

    connection.commit()
    connection.close()


# ==========================================================
# POMODORO FUNCTIONS
# ==========================================================

def add_pomodoro(task_id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        UPDATE tasks

        SET pomodoros = pomodoros + 1

        WHERE id = ?

    """, (task_id,))

    connection.commit()
    connection.close()


def get_task(task_id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""

        SELECT
            id,
            title,
            category,
            priority,
            due_date,
            completed,
            pomodoros

        FROM tasks

        WHERE id = ?

    """, (task_id,))

    task = cursor.fetchone()

    connection.close()

    return task