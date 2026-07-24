import customtkinter as ctk

from ui.sidebar import Sidebar
from ui.dashboard_page import DashboardPage
from ui.pomodoro_page import PomodoroPage
from ui.tasks_page import TasksPage
from ui.statistics_page import StatisticsPage
from ui.calendar_page import CalendarPage
from ui.history_page import HistoryPage
from ui.settings_page import SettingsPage
from ui.about_page import AboutPage


class MainWindow(ctk.CTk):

    def __init__(self):

        super().__init__()

        # ---------------- Window ---------------- #

        self.title("FocusFlow")
        self.geometry("1400x850")
        self.minsize(1200, 700)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # ---------------- Grid ---------------- #

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- Sidebar ---------------- #

        self.sidebar = Sidebar(
            self,
            self.change_page
        )

        self.sidebar.grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="ns"
        )

        # ---------------- Top Bar ---------------- #

        self.topbar = ctk.CTkFrame(
            self,
            height=70,
            corner_radius=0
        )

        self.topbar.grid(
            row=0,
            column=1,
            sticky="ew"
        )

        self.topbar.grid_propagate(False)

        # ---------------- Content ---------------- #

        self.content = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.content.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=20,
            pady=20
        )

        # ---------------- Title ---------------- #

        self.page_title = ctk.CTkLabel(
            self.topbar,
            text="Dashboard",
            font=("Segoe UI", 28, "bold")
        )

        self.page_title.pack(
            side="left",
            padx=25
        )

        # ---------------- Search ---------------- #

        self.search = ctk.CTkEntry(
            self.topbar,
            width=300,
            placeholder_text="Search..."
        )

        self.search.pack(
            side="right",
            padx=20,
            pady=15
        )

        # ---------------- Pages ---------------- #

        self.pages = {

            "Dashboard": DashboardPage(self.content),

            "Pomodoro": PomodoroPage(self.content),

            "Tasks": TasksPage(self.content, self),

            "Statistics": StatisticsPage(self.content),

            "Calendar": CalendarPage(self.content),

            "History": HistoryPage(self.content),

            "Settings": SettingsPage(self.content),

            "About": AboutPage(self.content)

        }

        self.show_page("Dashboard")

    # ===================================================

    def show_page(self, page):

        for frame in self.pages.values():
            frame.pack_forget()

        self.pages[page].pack(
            fill="both",
            expand=True
        )

        self.page_title.configure(
            text=page
        )

        if page == "Dashboard":

            try:
                self.pages["Dashboard"].refresh()
            except Exception:
                pass

    # ===================================================

    def change_page(self, page):

        self.show_page(page)