import sqlite3
import csv
from tkinter import filedialog

DB = "database/focusflow.db"


def export_sessions_csv():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            completed_at,
            minutes
        FROM sessions
        ORDER BY completed_at
    """)

    rows = cursor.fetchall()

    conn.close()

    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[
            ("CSV File", "*.csv")
        ],
        initialfile="focusflow_statistics.csv"
    )

    if not filename:
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Date",
            "Focus Minutes"
        ])

        writer.writerows(rows)