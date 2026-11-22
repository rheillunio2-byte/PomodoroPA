"""Session history, grouped by day."""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from services.history_service import get_history
from ui import theme
from ui.dashboard_page import hours_text
from ui.pages_base import BasePage
from ui.tasks_page import entry
from ui.widgets.components import Card, Pill, empty_state, icon, label, stat_tile

KIND = {"Work": ("timer", "tomato", "Focus"), "Short Break": ("coffee", "leaf", "Short break"),
        "Long Break": ("moon", "sky", "Long break")}
LIMIT = 300


def day_heading(day_text: str, today: date | None = None) -> str:
    today = today or date.today()
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        return day_text
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    return day.strftime("%A, %B %d")


class HistoryPage(BasePage):
    title = "History"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._job = None

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))
        self.search = entry(bar, "Search by task, type or date")
        self.search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search.bind("<KeyRelease>", lambda e: self._debounce())
        self.range = self._segment(bar, ["All Time", "Today", "This Week", "This Month"])
        self.kind = self._segment(bar, ["All", "Work", "Breaks"])

        tiles = ctk.CTkFrame(self, fg_color="transparent")
        tiles.pack(fill="x", pady=(0, 10))
        self.counters = []
        for i, (title, icon_name, token, fmt) in enumerate([
                ("Sessions", "timer", "tomato", None), ("Time", "clock", "sun", hours_text),
                ("Average session", "target", "leaf", lambda v: f"{int(round(v))} min")]):
            card, value = stat_tile(tiles, title, icon_name, token, *([fmt] if fmt else []))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == 2 else 6))
            tiles.grid_columnconfigure(i, weight=1, uniform="h")
            self.counters.append(value)

        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True)

    def _segment(self, parent, values):
        seg = ctk.CTkSegmentedButton(
            parent, values=values, command=lambda v: self.load_history(), height=34, corner_radius=10,
            font=theme.font(11, "bold"), fg_color=theme.pair("surface2"), unselected_color=theme.pair("surface2"),
            unselected_hover_color=theme.pair("surface3"), selected_color=theme.pair("tomato"),
            selected_hover_color=theme.pair("tomato_hi"), text_color=theme.pair("text"))
        seg.set(values[0])
        seg.pack(side="left", padx=4)
        return seg

    def on_show(self) -> None:
        self.load_history()

    def _debounce(self) -> None:
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(160, self.load_history)

    def load_history(self) -> None:
        for w in self.list.winfo_children():
            w.destroy()
        rows = get_history(self.range.get(), self.search.get(), self.kind.get())
        work = [r for r in rows if r[2] == "Work"]
        minutes = sum(r[1] or 0 for r in work)
        self.counters[0].set(len(work))
        self.counters[1].set(minutes)
        self.counters[2].set(round(minutes / len(work)) if work else 0)

        if not rows:
            empty_state(self.list, "history", "No sessions here", "Finish a Pomodoro and it will be logged automatically.",
                        ("Start the timer", self.app.toggle_timer)).pack(pady=20)
            return
        current = None
        for completed_at, mins, kind, task_title in rows[:LIMIT]:
            day, _, clock = (completed_at or "").partition(" ")
            if day != current:
                current = day
                label(self.list, day_heading(day), 13, "bold", tone="muted", anchor="w").pack(fill="x", padx=6, pady=(14, 4))
            icon_name, token, name = KIND.get(kind, ("timer", "muted", kind))
            row = Card(self.list, corner_radius=12)
            row.pack(fill="x", pady=3, padx=2)
            chip = ctk.CTkFrame(row, width=36, height=36, corner_radius=11, fg_color=theme.tint(token, 0.18))
            chip.pack(side="left", padx=(12, 12), pady=10)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text="", image=icon(icon_name, 18, token)).pack(expand=True)
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left")
            label(text, name if not task_title else f"{name} · {task_title}", 13, "bold", anchor="w").pack(anchor="w")
            label(text, clock[:5], 11, tone="muted", anchor="w").pack(anchor="w")
            Pill(row, f"{mins} min", token).pack(side="right", padx=14)
        if len(rows) > LIMIT:
            label(self.list, f"Showing the latest {LIMIT} of {len(rows)} sessions. Narrow the range to see the rest.",
                  11, tone="faint").pack(pady=12)
