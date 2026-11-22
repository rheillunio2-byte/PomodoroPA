"""Calendar: see and plan tasks by due date."""
from __future__ import annotations

from datetime import date, datetime

import customtkinter as ctk

from services import calendar_service
from ui import theme
from ui.pages_base import BasePage
from ui.widgets.components import Button, Card, Pill, empty_state, heading, icon, label
from ui.widgets.month_grid import MonthGrid

PRIORITY_TOKEN = {"Urgent": "plum", "High": "danger", "Medium": "sun", "Low": "muted"}


class CalendarPage(BasePage):
    title = "Calendar"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left = Card(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        head = ctk.CTkFrame(left, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 4))
        self.month_label = label(head, "", 18, "bold")
        self.month_label.pack(side="left")
        Button(head, "", lambda: self.step(1), kind="ghost", icon_name="chevron-right", width=36).pack(side="right")
        Button(head, "", lambda: self.step(-1), kind="ghost", icon_name="chevron-left", width=36).pack(side="right", padx=4)
        Button(head, "Today", self.go_today, kind="ghost", width=76).pack(side="right", padx=4)
        self.grid_widget = MonthGrid(left, on_select=self._selected)
        self.grid_widget.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        right.grid_rowconfigure(0, weight=3, uniform="r")
        right.grid_rowconfigure(1, weight=2, uniform="r")
        right.grid_columnconfigure(0, weight=1)

        self.day_card = Card(right)
        self.day_card.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        self.day_title = heading(self.day_card, "", 16)
        self.day_title.pack(anchor="w", padx=18, pady=(14, 4))
        self.day_list = ctk.CTkScrollableFrame(self.day_card, fg_color="transparent")
        self.day_list.pack(fill="both", expand=True, padx=8)
        Button(self.day_card, "Add a task for this day", self._add_for_day, kind="secondary", icon_name="plus",
               width=200).pack(pady=12)

        self.soon_card = Card(right)
        self.soon_card.grid(row=1, column=0, sticky="nsew", pady=(7, 0))

    # ------------------------------------------------------------------ lifecycle

    def on_show(self) -> None:
        self._refresh()

    def go_today(self) -> None:
        today = date.today()
        self.grid_widget.set_month(today.year, today.month)
        self.grid_widget.select(today)
        self._refresh()

    def step(self, direction: int) -> None:
        month = self.grid_widget.month + direction
        year = self.grid_widget.year
        if month == 0:
            month, year = 12, year - 1
        elif month == 13:
            month, year = 1, year + 1
        self.grid_widget.set_month(year, month, direction)
        self._refresh(day_panel=False)

    def _selected(self, day: date) -> None:
        self._refresh()

    def _refresh(self, day_panel: bool = True) -> None:
        g = self.grid_widget
        self.month_label.configure(text=date(g.year, g.month, 1).strftime("%B %Y"))
        g.set_summary(calendar_service.get_month_summary(g.year, g.month))
        if day_panel:
            self._load_day()
        self._load_soon()

    # --------------------------------------------------------------------- panels

    def _load_day(self) -> None:
        day = self.grid_widget.selected
        self.day_title.configure(text=day.strftime("%A, %B %d"))
        for w in self.day_list.winfo_children():
            w.destroy()
        tasks = calendar_service.get_tasks_by_date(day.isoformat())
        if not tasks:
            empty_state(self.day_list, "calendar", "Nothing due", "A clear day. Add something if you like.").pack()
            return
        for _, title, category, priority, completed in tasks:
            row = ctk.CTkFrame(self.day_list, fg_color=theme.pair("surface2"), corner_radius=10)
            row.pack(fill="x", pady=3, padx=4)
            ctk.CTkLabel(row, text="", image=icon("check" if completed else "timer", 16, "leaf" if completed else "muted")
                         ).pack(side="left", padx=(12, 8), pady=10)
            label(row, title, 12, "bold", tone="muted" if completed else "text", anchor="w").pack(side="left")
            Pill(row, priority, PRIORITY_TOKEN.get(priority, "muted")).pack(side="right", padx=10)

    def _load_soon(self) -> None:
        for w in self.soon_card.winfo_children():
            w.destroy()
        heading(self.soon_card, "Coming up", 16).pack(anchor="w", padx=18, pady=(14, 4))
        overdue = calendar_service.get_overdue_tasks(3)
        upcoming = calendar_service.get_upcoming_tasks(4)
        if not overdue and not upcoming:
            label(self.soon_card, "No deadlines ahead.", 12, tone="muted").pack(anchor="w", padx=18, pady=6)
            return
        today = date.today()
        for title, due, priority in overdue:
            self._soon_row(title, "Overdue", "danger", priority)
        for title, due, priority in upcoming:
            days = (datetime.strptime(due, "%Y-%m-%d").date() - today).days
            when = "Today" if days == 0 else "Tomorrow" if days == 1 else f"In {days} days"
            self._soon_row(title, when, PRIORITY_TOKEN.get(priority, "muted"), priority)

    def _soon_row(self, title: str, when: str, token: str, priority: str) -> None:
        row = ctk.CTkFrame(self.soon_card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=2)
        ctk.CTkLabel(row, text="●", text_color=theme.pair(PRIORITY_TOKEN.get(priority, "muted")),
                     font=theme.font(12)).pack(side="left")
        label(row, title, 12, anchor="w").pack(side="left", padx=8)
        label(row, when, 11, "bold" if when == "Overdue" else "normal", tone=token if when == "Overdue" else "muted").pack(side="right")

    def _add_for_day(self) -> None:
        self.app.show_page("Tasks")
        self.app.page("Tasks").prefill_due(self.grid_widget.selected.isoformat())
