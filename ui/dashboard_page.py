"""Dashboard: today at a glance."""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from services import chart_service, task_service
from services.achievement_service import get_achievements
from services.dashboard_service import get_dashboard_stats
from ui import theme
from ui.pages_base import BasePage
from ui.widgets.charts import BarChart
from ui.widgets.components import Button, Card, Pill, heading, icon, label, stat_tile, empty_state
from ui.widgets.ring import Ring
from ui.widgets.rotating_text import RotatingText

WORDS = ["focused", "consistent", "unstoppable", "productive"]
PRIORITY_TOKEN = {"Urgent": "plum", "High": "danger", "Medium": "sun", "Low": "muted"}


def greeting(hour: int | None = None) -> str:
    hour = datetime.now().hour if hour is None else hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"


def hours_text(minutes: float) -> str:
    minutes = int(round(minutes))
    return f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes} min"


class DashboardPage(BasePage):
    title = "Dashboard"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.body = self.scroller()

        # -- hero ---------------------------------------------------------------
        hero = ctk.CTkFrame(self.body, fg_color="transparent")
        hero.pack(fill="x", pady=(0, 18))
        left = ctk.CTkFrame(hero, fg_color="transparent")
        left.pack(side="left")
        self.greeting = label(left, "", 13, tone="muted", anchor="w")
        self.greeting.pack(anchor="w")
        line = ctk.CTkFrame(left, fg_color="transparent")
        line.pack(anchor="w", pady=(2, 0))
        label(line, "Stay", 30, "bold", anchor="w").pack(side="left", padx=(0, 12))
        self.words = RotatingText(line, WORDS, font_size=24, weight="bold", effect="slide", direction="up",
                                  highlight=True, highlight_color="tomato", stagger_duration=0.025,
                                  stagger_from="last", rotation_interval=2600, bg="bg", pause_on_hover=True,
                                  animate=bool(app.settings["animations"]))
        self.words.pack(side="left", pady=(4, 0))
        Button(hero, "Start focusing", lambda: app.toggle_timer(), kind="primary", icon_name="play",
               width=170, height=44).pack(side="right")

        # -- stat tiles ----------------------------------------------------------
        tiles = ctk.CTkFrame(self.body, fg_color="transparent")
        tiles.pack(fill="x")
        specs = [("Tasks completed", "check", "leaf"), ("Tasks pending", "tasks", "sky"),
                 ("Focus sessions", "timer", "tomato"), ("Time focused", "clock", "sun"),
                 ("Day streak", "flame", "plum")]
        self.tiles = []
        for i, (title, icon_name, token) in enumerate(specs):
            fmt = hours_text if title == "Time focused" else (lambda v: f"{int(round(v))}")
            card, value = stat_tile(tiles, title, icon_name, token, fmt)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 4 else 7))
            tiles.grid_columnconfigure(i, weight=1, uniform="tile")
            self.tiles.append(value)

        # -- chart + goal --------------------------------------------------------
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=14)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        chart_card = Card(row)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        heading(chart_card, "Focus time this week").pack(anchor="w", padx=18, pady=(14, 0))
        self.chart = BarChart(chart_card, height=210)
        self.chart.empty_text = "Finish a session and your week fills in here"
        self.chart.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        goal_card = Card(row)
        goal_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        heading(goal_card, "Today's goal").pack(anchor="w", padx=18, pady=(14, 0))
        self.goal_ring = Ring(goal_card, size=150, thickness=12, bg="surface", main_pt=26, sub_pt=10)
        self.goal_ring.pack(pady=(8, 4))
        self.goal_note = label(goal_card, "", 11, tone="muted", wraplength=180)
        self.goal_note.pack(pady=(0, 14))

        # -- up next + achievements ----------------------------------------------
        self.next_card = Card(self.body)
        self.next_card.pack(fill="x", pady=(0, 14))
        self.badge_card = Card(self.body)
        self.badge_card.pack(fill="x", pady=(0, 20))

    # ------------------------------------------------------------------- loading

    def on_show(self) -> None:
        self.greeting.configure(text=f"{greeting()}  ·  {datetime.now().strftime('%A, %B %d')}")
        stats = get_dashboard_stats()
        values = [stats["completed"], stats["pending"], stats["pomodoros"], stats["focus_minutes"], stats["streak"]]
        for tile, value in zip(self.tiles, values):
            tile.set(value)

        rows = chart_service.daily_focus(7)
        self.chart.set_data([(datetime.strptime(d, "%Y-%m-%d").strftime("%a"), m) for d, m, _ in rows], "min")

        goal = max(1, stats["daily_goal"])
        done = stats["today_pomodoros"]
        self.goal_ring.set_colors("Work" if done < goal else "Short Break")
        self.goal_ring.animate_to(min(1.0, done / goal))
        self.goal_ring.set_text(f"{done}/{goal}", "sessions")
        self.goal_note.configure(
            text="Goal reached. Everything from here is a bonus." if done >= goal else
            f"{goal - done} more to hit today's goal." if done else "Your first session sets the pace.")
        self._load_next()
        self._load_badges()

    def _load_next(self) -> None:
        for w in self.next_card.winfo_children():
            w.destroy()
        heading(self.next_card, "Up next").pack(anchor="w", padx=18, pady=(14, 6))
        tasks = task_service.get_tasks(status="Active")[:4]
        if not tasks:
            empty_state(self.next_card, "tasks", "Nothing queued", "Add a task and it shows up here, most urgent first.",
                        ("Add a task", self.app.new_task)).pack()
            return
        for task_id, title, category, priority, due, _, pomodoros in tasks:
            row = ctk.CTkFrame(self.next_card, fg_color=theme.pair("surface2"), corner_radius=12)
            row.pack(fill="x", padx=14, pady=4)
            label(row, title, 13, "bold", anchor="w").pack(side="left", padx=14, pady=10)
            Pill(row, priority, PRIORITY_TOKEN.get(priority, "muted")).pack(side="left")
            if due:
                label(row, f"due {due}", 11, tone="muted").pack(side="left", padx=10)
            Button(row, "Focus", lambda i=task_id, t=title: self._focus(i, t), kind="ghost", icon_name="play",
                   width=90, height=30).pack(side="right", padx=10)
        ctk.CTkFrame(self.next_card, height=8, fg_color="transparent").pack()

    def _focus(self, task_id: int, title: str) -> None:
        self.app.pomodoro.set_current_task(task_id, title)
        self.app.show_page("Pomodoro")

    def _load_badges(self) -> None:
        for w in self.badge_card.winfo_children():
            w.destroy()
        badges = get_achievements()
        unlocked = sum(b["unlocked"] for b in badges)
        head = ctk.CTkFrame(self.badge_card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 6))
        heading(head, "Achievements").pack(side="left")
        label(head, f"{unlocked} of {len(badges)} unlocked", 11, tone="muted").pack(side="right")
        grid = ctk.CTkFrame(self.badge_card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for i, b in enumerate(badges):
            tile = ctk.CTkFrame(grid, corner_radius=12, fg_color=theme.pair("surface2"))
            tile.grid(row=i // 5, column=i % 5, sticky="nsew", padx=4, pady=4)
            grid.grid_columnconfigure(i % 5, weight=1, uniform="badge")
            token = "sun" if b["unlocked"] else "faint"
            chip = ctk.CTkFrame(tile, width=34, height=34, corner_radius=10, fg_color=theme.tint(token, 0.2, "surface2"))
            chip.pack(anchor="w", padx=12, pady=(12, 0))
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text="", image=icon(b["icon"] if b["unlocked"] else "lock", 18, token)).pack(expand=True)
            label(tile, b["title"], 12, "bold", tone="text" if b["unlocked"] else "muted", anchor="w").pack(anchor="w", padx=12, pady=(6, 0))
            if b["unlocked"]:
                label(tile, b["description"], 10, tone="muted", anchor="w", wraplength=150, justify="left").pack(anchor="w", padx=12, pady=(0, 12))
            else:
                bar = ctk.CTkProgressBar(tile, height=5, corner_radius=3, fg_color=theme.pair("surface3"),
                                         progress_color=theme.pair("tomato"))
                bar.set(b["progress"] / b["target"])
                bar.pack(fill="x", padx=12, pady=(6, 2))
                label(tile, f"{b['progress']} / {b['target']}", 10, tone="faint", anchor="w").pack(anchor="w", padx=12, pady=(0, 10))
