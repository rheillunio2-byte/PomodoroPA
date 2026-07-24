import sqlite3

DB = "database/focusflow.db"


def get_achievements():

    connection = sqlite3.connect(DB)
    cursor = connection.cursor()

    # Total pomodoros
    cursor.execute("""
        SELECT IFNULL(SUM(pomodoros),0)
        FROM tasks
    """)
    pomodoros = cursor.fetchone()[0]

    # Completed tasks
    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE completed=1
    """)
    completed = cursor.fetchone()[0]

    connection.close()

    achievements = []

    if pomodoros >= 1:
        achievements.append(("🥉", "First Pomodoro"))

    if pomodoros >= 10:
        achievements.append(("🥈", "10 Pomodoros"))

    if pomodoros >= 50:
        achievements.append(("🥇", "50 Pomodoros"))

    if pomodoros >= 100:
        achievements.append(("🏆", "100 Pomodoros"))

    if completed >= 10:
        achievements.append(("✅", "10 Completed Tasks"))

    if completed >= 50:
        achievements.append(("⭐", "50 Completed Tasks"))

    if completed >= 100:
        achievements.append(("💯", "100 Completed Tasks"))

    return achievements