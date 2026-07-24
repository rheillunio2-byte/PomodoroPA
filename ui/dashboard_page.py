import customtkinter as ctk
from services.achievement_service import get_achievements
from services.streak_service import get_current_streak
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from services.chart_service import weekly_productivity

from datetime import datetime

from services.dashboard_service import get_dashboard_stats


class DashboardPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=("Segoe UI", 34, "bold")
        )

        title.pack(
            anchor="w",
            padx=30,
            pady=(25, 5)
        )

        today = datetime.now().strftime("%A, %B %d, %Y")

        self.date_label = ctk.CTkLabel(
            self,
            text=today,
            font=("Segoe UI", 16)
        )

        self.date_label.pack(
            anchor="w",
            padx=32,
            pady=(0, 20)
        )

        self.cards = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.cards.pack(
            fill="x",
            padx=25
        )

        self.completed = self.create_card(
            "✅ Completed Tasks",
            "#16a34a"
        )

        self.pending = self.create_card(
            "📋 Pending Tasks",
            "#2563eb"
        )

        self.pomodoros = self.create_card(
            "🍅 Pomodoros",
            "#dc2626"
        )

        self.focus = self.create_card(
            "⏱ Focus Minutes",
            "#f59e0b"
        )

        self.streak = self.create_card(
            "🔥 Streak",
            "#7c3aed"
        )

        # ============================
        # Productivity Chart
        # ============================

        self.chart_frame = ctk.CTkFrame(self)

        self.chart_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=25
        )

        # ============================
        # Achievements
        # ============================

        self.badge_frame = ctk.CTkFrame(self)

        self.badge_frame.pack(
            fill="x",
            padx=25,
            pady=(10, 25)
        )

        self.refresh()

    def load_achievements(self):

        for widget in self.badge_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.badge_frame,
            text="🏆 Achievements",
            font=("Segoe UI", 22, "bold")
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 15)
        )

        achievements = get_achievements()

        if not achievements:

            ctk.CTkLabel(
                self.badge_frame,
                text="No achievements unlocked yet."
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 10)
            )

            return

        for icon, title in achievements:

            ctk.CTkLabel(
                self.badge_frame,
                text=f"{icon}  {title}",
                font=("Segoe UI", 16)
            ).pack(
                anchor="w",
                padx=25,
                pady=3
            )

    def draw_chart(self):

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        data = weekly_productivity()

        dates = [row[0] for row in data]
        values = [row[1] for row in data]

        figure = Figure(
            figsize=(8, 4),
            dpi=100
        )

        ax = figure.add_subplot(111)

        ax.bar(dates, values)

        ax.set_title("Weekly Productivity")
        ax.set_ylabel("Pomodoros")
        ax.tick_params(axis="x", rotation=30)

        canvas = FigureCanvasTkAgg(
            figure,
            self.chart_frame
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

    def create_card(self, title, color):

        card = ctk.CTkFrame(
            self.cards,
            width=240,
            height=130,
            corner_radius=18,
            fg_color=color
        )

        card.pack(
            side="left",
            expand=True,
            fill="both",
            padx=10
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI",16,"bold")
        ).pack(
            pady=(18,5)
        )

        value = ctk.CTkLabel(
            card,
            text="0",
            font=("Segoe UI",36,"bold")
        )

        value.pack()

        return value

    def refresh(self):

        stats = get_dashboard_stats()

        self.completed.configure(
            text=str(stats["completed"])
        )

        self.pending.configure(
            text=str(stats["pending"])
        )

        self.pomodoros.configure(
            text=str(stats["pomodoros"])
        )

        self.focus.configure(
            text=str(stats["focus_minutes"])
        )

        try:
            self.draw_chart()
        except Exception:
            pass

        self.streak.configure(
            text=f"{get_current_streak()} Days"
        )

        self.load_achievements()
