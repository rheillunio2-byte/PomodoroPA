import sqlite3
from datetime import datetime, timedelta

DB = "database/focusflow.db"


def get_current_streak():

    connection = sqlite3.connect(DB)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT DATE(completed_at)
        FROM sessions
        ORDER BY DATE(completed_at) DESC
    """)

    dates = [row[0] for row in cursor.fetchall()]

    connection.close()

    if not dates:
        return 0

    streak = 0
    current = datetime.now().date()

    for date_string in dates:

        saved_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

        if saved_date == current:

            streak += 1
            current -= timedelta(days=1)

        elif saved_date == current - timedelta(days=1) and streak == 0:

            streak += 1
            current = saved_date - timedelta(days=1)

        else:

            break

    return streak