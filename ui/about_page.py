"""About."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk

import config
from ui.engine.logo import render_logo
from ui.pages_base import BasePage
from ui.widgets.components import Button, Card, Pill, heading, icon, label

WHATS_NEW = [
    "Magnifying dock navigation and animated page titles",
    "A timer ring with a live window-title countdown, confetti and keyboard shortcuts",
    "Native animated charts and an activity heatmap, light and dark themes",
    "Ctrl+K command palette, quick due dates, reopen finished tasks",
    "Cursor trail, ring and click ripples (Windows)",
    "A rewritten timer engine, one shared database layer and a test suite",
]
FEATURES = [("timer", "Pomodoro timer", "Focus, short break and long break cycles"),
            ("tasks", "Task manager", "Categories, priorities and due dates"),
            ("stats", "Statistics", "Charts, heatmap and plain-language insights"),
            ("calendar", "Calendar", "Plan by due date"),
            ("history", "History", "Every session, grouped by day"),
            ("medal", "Achievements", "Badges with progress")]


class AboutPage(BasePage):
    title = "About"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        body = self.scroller()

        hero = Card(body)
        hero.pack(fill="x", pady=(0, 14))
        row = ctk.CTkFrame(hero, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=22)
        logo = render_logo(96)
        self._logo = ctk.CTkImage(light_image=logo, dark_image=logo, size=(96, 96))
        ctk.CTkLabel(row, text="", image=self._logo).pack(side="left", padx=(0, 22))
        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left")
        title = ctk.CTkFrame(text, fg_color="transparent")
        title.pack(anchor="w")
        label(title, config.APP_NAME, 30, "bold").pack(side="left")
        Pill(title, f"v{config.APP_VERSION}", "tomato").pack(side="left", padx=12, pady=(8, 0))
        label(text, config.APP_TAGLINE, 14, tone="muted", anchor="w").pack(anchor="w", pady=(2, 10))
        buttons = ctk.CTkFrame(text, fg_color="transparent")
        buttons.pack(anchor="w")
        Button(buttons, "View on GitHub", lambda: webbrowser.open(config.REPO_URL), kind="primary",
               icon_name="link", width=170).pack(side="left")
        Button(buttons, "Report an issue", lambda: webbrowser.open(config.REPO_URL + "/issues"), kind="ghost",
               width=150).pack(side="left", padx=8)

        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1, uniform="about")
        new = Card(grid)
        new.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        heading(new, f"New in {config.APP_VERSION}").pack(anchor="w", padx=20, pady=(16, 8))
        for item in WHATS_NEW:
            line = ctk.CTkFrame(new, fg_color="transparent")
            line.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(line, text="", image=icon("check", 14, "leaf")).pack(side="left", anchor="n", padx=(0, 8), pady=2)
            label(line, item, 12, tone="muted", anchor="w", justify="left", wraplength=380).pack(side="left")
        ctk.CTkFrame(new, height=14, fg_color="transparent").pack()

        feats = Card(grid)
        feats.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        heading(feats, "What's inside").pack(anchor="w", padx=20, pady=(16, 8))
        for icon_name, name, desc in FEATURES:
            line = ctk.CTkFrame(feats, fg_color="transparent")
            line.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(line, text="", image=icon(icon_name, 18, "tomato")).pack(side="left", padx=(0, 12))
            t = ctk.CTkFrame(line, fg_color="transparent")
            t.pack(side="left")
            label(t, name, 12, "bold", anchor="w").pack(anchor="w")
            label(t, desc, 11, tone="muted", anchor="w").pack(anchor="w")
        ctk.CTkFrame(feats, height=14, fg_color="transparent").pack()

        foot = Card(body)
        foot.pack(fill="x", pady=14)
        label(foot, f"Built by {config.APP_AUTHOR}  ·  Python, CustomTkinter, Pillow and SQLite  ·  "
                    f"{config.LICENSE_NAME} licensed", 12, tone="muted").pack(pady=16)
