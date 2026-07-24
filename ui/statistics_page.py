import customtkinter as ctk
from services.insight_service import generate_insights
from services.export_service import export_sessions_csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.chart_service import (
    weekly_productivity,
    task_categories,
    monthly_productivity
)

from services.statistics_service import get_statistics


class StatisticsPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.scroll.pack(
            fill="both",
            expand=True
        )

        title = ctk.CTkLabel(
            self.scroll,
            text="📊 Productivity Statistics",
            font=("Segoe UI", 32, "bold")
        )

        title.pack(
            anchor="w",
            padx=30,
            pady=(25, 20)
        )

        filter_frame = ctk.CTkFrame(
            self.scroll,
            fg_color="transparent"
        )

        filter_frame.pack(
            fill="x",
            padx=30,
            pady=(0,20)
        )

        self.current_filter = "All"

        for option in [
            "Today",
            "Week",
            "Month",
            "All"
        ]:

            ctk.CTkButton(
                filter_frame,
                text=option,
                width=120,
                command=lambda f=option: self.change_filter(f)
            ).pack(
                side="left",
                padx=5
            )

        # ===========================
        # CARD CONTAINER
        # ===========================

        self.cards = ctk.CTkFrame(
            self.scroll,
            fg_color="transparent"
        )

        self.cards.pack(
            fill="x",
            padx=20
        )

        self.sessions = self.create_card(
            "🍅 Pomodoros",
            "#dc2626"
        )

        self.focus = self.create_card(
            "⏱ Focus Minutes",
            "#2563eb"
        )

        self.today = self.create_card(
            "📅 Today",
            "#16a34a"
        )

        self.completed = self.create_card(
            "✅ Completed",
            "#7c3aed"
        )

        self.pending = self.create_card(
            "📋 Pending",
            "#f59e0b"
        )

        self.rate = self.create_card(
            "🎯 Completion %",
            "#0891b2"
        )

        self.refresh()

        self.chart_container = ctk.CTkFrame(
            self.scroll,
            fg_color="transparent"
        )

        self.chart_container.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        self.monthly_frame = ctk.CTkFrame(
            self.scroll
        )

        self.monthly_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0,20)
        )

        self.insight_frame = ctk.CTkFrame(
            self.scroll
        )

        self.insight_frame.pack(
            fill="x",
            padx=20,
            pady=20
        )

        self.chart_frame = ctk.CTkFrame(
            self.chart_container
        )

        self.chart_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0,10)
        )

        self.pie_frame = ctk.CTkFrame(
            self.chart_container
        )

        self.pie_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10,0)
        )

        self.draw_chart()
        self.draw_pie_chart()
        self.draw_monthly_chart()
        self.load_insights()

    def draw_pie_chart(self):

        for widget in self.pie_frame.winfo_children():
            widget.destroy()

        data = task_categories()

        if len(data) == 0:

            ctk.CTkLabel(
                self.pie_frame,
                text="No task data yet.",
                font=("Segoe UI",18)
            ).pack(
                pady=60
            )

            return

        labels = [row[0] for row in data]
        sizes = [row[1] for row in data]

        figure = Figure(
            figsize=(5,4),
            dpi=100
        )

        ax = figure.add_subplot(111)

        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90
        )

        ax.set_title(
            "Task Categories"
        )

        canvas = FigureCanvasTkAgg(
            figure,
            self.pie_frame
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

    def draw_monthly_chart(self):

        for widget in self.monthly_frame.winfo_children():
            widget.destroy()

        data = monthly_productivity()

        if len(data) == 0:

            ctk.CTkLabel(
                self.monthly_frame,
                text="No monthly data available.",
                font=("Segoe UI",18)
            ).pack(
                pady=60
            )

            return

        months = [row[0] for row in data]
        values = [row[1] for row in data]

        figure = Figure(
            figsize=(10,4),
            dpi=100
        )

        ax = figure.add_subplot(111)

        ax.plot(
            months,
            values,
            marker="o",
            linewidth=2
        )

        ax.set_title("Monthly Productivity Trend")
        ax.set_ylabel("Pomodoro Sessions")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(
            figure,
            self.monthly_frame
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        self.export_button = ctk.CTkButton(
            self.scroll,
            text="📄 Export Statistics (CSV)",
            width=250,
            height=45,
            command=export_sessions_csv
        )

        self.export_button.pack(
            pady=(10,25)
        )

    def create_card(self, title, color):

        card = ctk.CTkFrame(
            self.cards,
            width=190,
            height=120,
            fg_color=color,
            corner_radius=18
        )

        card.pack(
            side="left",
            expand=True,
            fill="both",
            padx=8
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 15, "bold")
        ).pack(
            pady=(18, 8)
        )

        value = ctk.CTkLabel(
            card,
            text="0",
            font=("Segoe UI", 30, "bold")
        )

        value.pack()

        return value

    def refresh(self):

        stats = get_statistics(
            self.current_filter
        )

        self.sessions.configure(
            text=str(stats["sessions"])
        )

        self.focus.configure(
            text=f'{stats["focus"]} min'
        )

        self.today.configure(
            text=f'{stats["today"]} min'
        )

        self.completed.configure(
            text=str(stats["completed"])
        )

        self.pending.configure(
            text=str(stats["pending"])
        )

        self.rate.configure(
            text=f'{stats["completion"]}%'
        )

        try:
            self.draw_chart()
            self.draw_pie_chart()
            self.draw_monthly_chart()
            self.load_insights()
        except Exception:
            pass

    def draw_chart(self):

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        data = weekly_productivity()

        if len(data) == 0:

            ctk.CTkLabel(
                self.chart_frame,
                text="No productivity data yet.",
                font=("Segoe UI",18)
            ).pack(
                pady=60
            )

            return

        dates = [row[0] for row in data]
        values = [row[1] for row in data]

        figure = Figure(
            figsize=(8,4),
            dpi=100
        )

        ax = figure.add_subplot(111)

        ax.bar(dates, values)

        ax.set_title("Weekly Productivity")

        ax.set_ylabel("Pomodoro Sessions")

        ax.tick_params(
            axis="x",
            rotation=25
        )

        canvas = FigureCanvasTkAgg(
            figure,
            self.chart_frame
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

    def change_filter(self, value):

        self.current_filter = value

        self.refresh()

    def load_insights(self):

        for widget in self.insight_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.insight_frame,
            text="🧠 AI Productivity Insights",
            font=("Segoe UI", 24, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,10)
        )

        for insight in generate_insights():

            ctk.CTkLabel(
                self.insight_frame,
                text=insight,
                justify="left",
                anchor="w",
                font=("Segoe UI",16)
            ).pack(
                anchor="w",
                padx=30,
                pady=3
            )