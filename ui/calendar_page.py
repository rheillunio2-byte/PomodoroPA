import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime
from services.calendar_service import (
    get_tasks_by_date,
    get_task_dates,
    get_upcoming_tasks
)

class CalendarPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="📅 Calendar",
            font=("Segoe UI", 30, "bold")
        )

        title.pack(
            anchor="w",
            padx=20,
            pady=20
        )

        content = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        content.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        left = ctk.CTkFrame(content)

        left.pack(
            side="left",
            fill="y",
            padx=(0,20)
        )

        right = ctk.CTkFrame(
            content
        )

        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.calendar = Calendar(
            left,
            selectmode="day",
            date_pattern="yyyy-mm-dd"
        )

        self.calendar.pack(
            padx=15,
            pady=15
        )

        self.calendar.bind(
            "<<CalendarSelected>>",
            self.load_tasks
        )

        self.upcoming_frame = ctk.CTkFrame(
            right
        )

        self.upcoming_frame.pack(
            fill="x",
            padx=20,
            pady=(15,20)
        )

        self.selected_label = ctk.CTkLabel(
            right,
            text="Tasks",
            font=("Segoe UI",22,"bold")
        )

        self.selected_label.pack(
            anchor="w",
            padx=20,
            pady=(20,10)
        )

        self.task_frame = ctk.CTkScrollableFrame(right)

        self.task_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0,20)
        )

        self.highlight_dates()
        self.load_upcoming()
        self.load_tasks()

    def load_tasks(self, event=None):

        for widget in self.task_frame.winfo_children():
            widget.destroy()

        selected = self.calendar.get_date()

        self.selected_label.configure(
            text=f"Tasks for {selected}"
        )

        tasks = get_tasks_by_date(selected)

        if len(tasks) == 0:

            ctk.CTkLabel(
                self.task_frame,
                text="No tasks scheduled.",
                font=("Segoe UI",18)
            ).pack(
                pady=40
            )

            return

        for _, title, category, priority, completed in tasks:

            icon = "✅" if completed else "⭕"

            ctk.CTkLabel(
                self.task_frame,
                text=f"{icon} {title} ({category}) • {priority}",
                anchor="w",
                font=("Segoe UI",16)
            ).pack(
                fill="x",
                padx=10,
                pady=6
            )

    def highlight_dates(self):

        dates = get_task_dates()

        for d in dates:

            try:

                self.calendar.calevent_create(
                    d,
                    "Task",
                    "task"
                )

            except Exception:
                pass

        self.calendar.tag_config(
            "task",
            background="#2563eb",
            foreground="white"
        )

    def refresh_calendar(self):

        self.calendar.calevent_remove("all")

        self.highlight_dates()

        self.load_upcoming()

        self.load_tasks()

    def load_upcoming(self):

        for widget in self.upcoming_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.upcoming_frame,
            text="📌 Upcoming Deadlines",
            font=("Segoe UI",20,"bold")
        ).pack(
            anchor="w",
            padx=15,
            pady=(10,10)
        )

        rows = get_upcoming_tasks()

        if not rows:

            ctk.CTkLabel(
                self.upcoming_frame,
                text="No upcoming tasks."
            ).pack(
                padx=20,
                pady=10,
                anchor="w"
            )

            return

        today = datetime.today().date()

        colors = {
            "Urgent": "#e74c3c",
            "High": "#f39c12",
            "Medium": "#3498db",
            "Low": "#27ae60"
        }

        for title, due, priority in rows:

            due_date = datetime.strptime(
                due,
                "%Y-%m-%d"
            ).date()

            days = (due_date - today).days

            if days == 0:
                when = "Today"
            elif days == 1:
                when = "Tomorrow"
            else:
                when = f"{days} days"

            row = ctk.CTkFrame(
                self.upcoming_frame,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=15,
                pady=4
            )

            ctk.CTkLabel(
                row,
                text="●",
                text_color=colors.get(priority, "white"),
                font=("Segoe UI",20)
            ).pack(
                side="left"
            )

            ctk.CTkLabel(
                row,
                text=f"{title} ({when})",
                font=("Segoe UI",15)
            ).pack(
                side="left",
                padx=8
            )
                