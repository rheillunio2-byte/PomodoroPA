import sqlite3
from datetime import datetime

DB = "database/focusflow.db"


def generate_insights():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    insights = []

    # -----------------------------
    # Completion Rate
    # -----------------------------

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed=1")
    completed_tasks = cursor.fetchone()[0]

    completion = 0

    if total_tasks > 0:
        completion = round(completed_tasks / total_tasks * 100)

    insights.append(f"✔ Task Completion Rate: {completion}%")

    # -----------------------------
    # Focus Minutes
    # -----------------------------

    cursor.execute("SELECT IFNULL(SUM(minutes),0) FROM sessions")
    total_minutes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    insights.append(f"🍅 Pomodoro Sessions: {total_sessions}")
    insights.append(f"⏱ Total Focus Time: {total_minutes} minutes")

    # -----------------------------
    # Average Minutes Per Day
    # -----------------------------

    cursor.execute("""
        SELECT COUNT(DISTINCT DATE(completed_at))
        FROM sessions
    """)

    active_days = cursor.fetchone()[0]

    average = 0

    if active_days > 0:
        average = round(total_minutes / active_days)

    insights.append(
        f"📊 Average Focus: {average} minutes/day"
    )

    # -----------------------------
    # Favorite Category
    # -----------------------------

    cursor.execute("""
        SELECT category,
               COUNT(*)

        FROM tasks

        GROUP BY category

        ORDER BY COUNT(*) DESC

        LIMIT 1
    """)

    row = cursor.fetchone()

    if row:
        insights.append(
            f"📂 Most Active Category: {row[0]}"
        )

    # -----------------------------
    # Best Weekday
    # -----------------------------

    cursor.execute("""
        SELECT
            strftime('%w', completed_at),
            COUNT(*)

        FROM sessions

        GROUP BY strftime('%w', completed_at)

        ORDER BY COUNT(*) DESC

        LIMIT 1
    """)

    days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    row = cursor.fetchone()

    if row:
        insights.append(
            f"🏆 Most Productive Day: {days[int(row[0])]}"
        )

    # -----------------------------
    # Personalized Recommendations
    # -----------------------------

    recommendations = []

    if completion < 50:
        recommendations.append(
            "Finish easier tasks first to build momentum."
        )

    elif completion < 80:
        recommendations.append(
            "You're close to excellent consistency. Aim for an 80%+ completion rate."
        )

    else:
        recommendations.append(
            "Excellent task completion. Maintain your current routine."
        )

    if average < 60:
        recommendations.append(
            "Increase your daily focus time to at least 60 minutes."
        )

    elif average < 120:
        recommendations.append(
            "Try reaching 120 focused minutes each day for stronger productivity."
        )

    else:
        recommendations.append(
            "Great focus habit. Remember to take regular breaks to avoid burnout."
        )

    if total_sessions < 20:
        recommendations.append(
            "Complete more Pomodoro sessions to improve your productivity history."
        )

    elif total_sessions > 100:
        recommendations.append(
            "You've built a strong productivity record. Consider setting higher weekly goals."
        )

    insights.append("")
    insights.append("💡 Personalized Recommendations")

    for recommendation in recommendations:
        insights.append(f"• {recommendation}")

    conn.close()

    return insights