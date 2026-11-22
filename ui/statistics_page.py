"""Statistics: range-aware numbers, charts, heatmap, insights, export."""
from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from services import chart_service
from services.export_service import export_sessions_csv, export_tasks_csv
from services.insight_service import get_insights
from services.statistics_service import get_statistics
from ui import theme
from ui.dashboard_page import hours_text
from ui.pages_base import BasePage
from ui.widgets.charts import BarChart, DonutChart, Heatmap
from ui.widgets.components import Button, Card, heading, icon, label, stat_tile

RANGES = ["Today", "Week", "Month", "All"]


class StatisticsPage(BasePage):
    title = "Statistics"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.range = "Week"
        body = self.body = self.scroller()

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 14))
        self.range_picker = ctk.CTkSegmentedButton(
            top, values=RANGES, command=self._set_range, height=36, corner_radius=10, font=theme.font(12, "bold"),
            fg_color=theme.pair("surface2"), unselected_color=theme.pair("surface2"),
            unselected_hover_color=theme.pair("surface3"), selected_color=theme.pair("tomato"),
            selected_hover_color=theme.pair("tomato_hi"), text_color=theme.pair("text"))
        self.range_picker.set(self.range)
        self.range_picker.pack(side="left")
        Button(top, "Export tasks", self.export_tasks, kind="ghost", icon_name="download", width=130).pack(side="right")
        Button(top, "Export sessions", self.export_sessions, kind="ghost", icon_name="download", width=150).pack(side="right", padx=8)

        tiles = ctk.CTkFrame(body, fg_color="transparent")
        tiles.pack(fill="x")
        specs = [("Focus sessions", "timer", "tomato", None), ("Time focused", "clock", "sun", hours_text),
                 ("Today", "target", "leaf", hours_text), ("Tasks completed", "check", "sky", None),
                 ("Tasks pending", "tasks", "plum", None), ("Completion rate", "stats", "leaf", lambda v: f"{v:.0f}%")]
        self.values = []
        for i, (title, icon_name, token, fmt) in enumerate(specs):
            card, value = stat_tile(tiles, title, icon_name, token, *([fmt] if fmt else []))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == 5 else 6))
            tiles.grid_columnconfigure(i, weight=1, uniform="stat")
            self.values.append(value)

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=14)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)
        bar_card = Card(row)
        bar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.bar_title = heading(bar_card, "Focus minutes")
        self.bar_title.pack(anchor="w", padx=18, pady=(14, 0))
        self.bars = BarChart(bar_card, height=240)
        self.bars.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        donut_card = Card(row)
        donut_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        heading(donut_card, "Tasks by category").pack(anchor="w", padx=18, pady=(14, 0))
        self.donut = DonutChart(donut_card, height=240)
        self.donut.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        heat_card = Card(body)
        heat_card.pack(fill="x", pady=(0, 14))
        heading(heat_card, "Last 12 weeks").pack(anchor="w", padx=18, pady=(14, 0))
        self.heat = Heatmap(heat_card, height=170)
        self.heat.pack(fill="x", padx=12, pady=(4, 12))

        self.insights = Card(body)
        self.insights.pack(fill="x", pady=(0, 20))

    def on_show(self) -> None:
        self.refresh()

    def _set_range(self, value: str) -> None:
        self.range = value
        self.refresh()

    def refresh(self) -> None:
        stats = get_statistics(self.range)
        for tile, value in zip(self.values, [stats["sessions"], stats["focus"], stats["today"], stats["completed"],
                                             stats["pending"], stats["completion"]]):
            tile.set(value)
        title, rows = chart_service.focus_series(self.range)
        self.bar_title.configure(text=title)
        self.bars.empty_text = "No focus time in this range yet"
        self.bars.set_data(rows, "min")
        self.donut.set_data(chart_service.task_categories())
        start, data = chart_service.activity_heatmap(12)
        self.heat.set_data(start, data, 12)
        self._load_insights()

    def _load_insights(self) -> None:
        for w in self.insights.winfo_children():
            w.destroy()
        info = get_insights()
        heading(self.insights, "Insights").pack(anchor="w", padx=18, pady=(14, 8))
        grid = ctk.CTkFrame(self.insights, fg_color="transparent")
        grid.pack(fill="x", padx=12)
        for i, (icon_name, name, value) in enumerate(info["metrics"]):
            cell = ctk.CTkFrame(grid, fg_color=theme.pair("surface2"), corner_radius=12)
            cell.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            grid.grid_columnconfigure(i % 3, weight=1, uniform="ins")
            ctk.CTkLabel(cell, text="", image=icon(icon_name, 18, "tomato")).pack(side="left", padx=(14, 10), pady=14)
            text = ctk.CTkFrame(cell, fg_color="transparent")
            text.pack(side="left", pady=10)
            label(text, value, 15, "bold", anchor="w").pack(anchor="w")
            label(text, name, 11, tone="muted", anchor="w").pack(anchor="w")
        if info["tips"]:
            tips = ctk.CTkFrame(self.insights, fg_color="transparent")
            tips.pack(fill="x", padx=18, pady=(10, 16))
            for tip in info["tips"]:
                row = ctk.CTkFrame(tips, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text="", image=icon("sparkle", 14, "sun")).pack(side="left", padx=(0, 8))
                label(row, tip, 12, tone="muted", anchor="w", justify="left", wraplength=900).pack(side="left")

    # ---------------------------------------------------------------- exporting

    def _export(self, writer, default_name: str, noun: str) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
                                            initialfile=default_name)
        if not path:
            return
        try:
            count = writer(path)
        except OSError as error:
            self.app.toast(f"Couldn't save the file: {error.strerror or error}", "error")
            return
        self.app.toast(f"Exported {count} {noun}", "success")

    def export_sessions(self) -> None:
        self._export(export_sessions_csv, "focusflow_sessions.csv", "sessions")

    def export_tasks(self) -> None:
        self._export(export_tasks_csv, "focusflow_tasks.csv", "tasks")
