"""The application shell: header, pages, dock, toasts, shortcuts, cursor FX."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from PIL import ImageTk

import config
from services import db, task_service
from services.settings_service import get_settings, update_settings
from ui import anim, theme
from ui.engine.dock_engine import DockItem
from ui.engine.logo import render_logo
from ui.widgets.command_palette import CommandPalette
from ui.widgets.components import Button, ToastHost, icon
from ui.widgets.cursor_fx import CursorFX
from ui.widgets.dock import Dock
from ui.widgets.rotating_text import RotatingText

from ui.about_page import AboutPage
from ui.calendar_page import CalendarPage
from ui.dashboard_page import DashboardPage
from ui.history_page import HistoryPage
from ui.pomodoro_page import PomodoroPage
from ui.settings_page import SettingsPage
from ui.statistics_page import StatisticsPage
from ui.tasks_page import TasksPage

PAGES = {
    "Dashboard": (DashboardPage, "home"),
    "Pomodoro": (PomodoroPage, "timer"),
    "Tasks": (TasksPage, "tasks"),
    "Statistics": (StatisticsPage, "stats"),
    "Calendar": (CalendarPage, "calendar"),
    "History": (HistoryPage, "history"),
    "Settings": (SettingsPage, "settings"),
    "About": (AboutPage, "about"),
}


class MainWindow(ctk.CTk):

    PAGE_NAMES = list(PAGES)

    def __init__(self):
        db.init_db()
        self.settings = get_settings()
        super().__init__()
        anim.init(self)
        theme.init_fonts(self)
        theme.apply(self.settings["theme"])
        anim.set_enabled(bool(self.settings["animations"]))

        self.title(config.APP_NAME)
        self.geometry("1360x860")
        self.minsize(1080, 680)
        self.configure(fg_color=theme.pair("bg"))
        self._icon = ImageTk.PhotoImage(render_logo(64))
        self.after(300, lambda: self.iconphoto(True, self._icon))     # CTk resets the icon at ~200 ms

        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=28, pady=(4, 0))
        self._build_dock()

        self.toaster = ToastHost(self, bottom_offset=140)
        self.palette = CommandPalette(self)
        self.cursor = CursorFX(self)
        self._bind_keys()

        self.pomodoro = self.page("Pomodoro")           # the timer must exist from the start
        self.show_page("Dashboard", animate=False)
        self.refresh_badges()
        self.after(400, self._start_cursor)
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ------------------------------------------------------------------ building

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent", height=64)
        bar.grid(row=0, column=0, sticky="ew", padx=28, pady=(14, 0))
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        self.title_text = RotatingText(
            bar, self.PAGE_NAMES, font_size=26, weight="bold", effect="slide", direction="up",
            stagger_duration=0.018, stagger_from="first", auto=False, rotation_interval=999999,
            bg="bg", overflow_hidden=True, animate=bool(self.settings["animations"]))
        self.title_text.grid(row=0, column=0, sticky="w", pady=10)
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        Button(right, "Search or jump to…   Ctrl K", self.palette_toggle, kind="ghost",
               icon_name="search", width=250).pack(side="left", padx=(0, 8))
        self.theme_button = Button(right, "", self.toggle_theme, kind="ghost", width=38,
                                   icon_name="sun" if theme.mode() == "dark" else "moon")
        self.theme_button.pack(side="left")

    def _build_dock(self) -> None:
        items = []
        for name, (_, icon_name) in PAGES.items():
            if name == "Settings":
                items.append(DockItem(separator=True))
            items.append(DockItem(key=name, label=name, icon=icon_name,
                                  on_click=lambda n=name: self.show_page(n), menu=self._menu_for(name)))
        self.dock = Dock(self, items, animate=bool(self.settings["animations"]))
        self.dock.grid(row=2, column=0, sticky="ew")

    def _menu_for(self, name: str):
        menus = {
            "Dashboard": [("Refresh", lambda: self.page("Dashboard").on_show())],
            "Pomodoro": [("Start / pause", self.toggle_timer), ("Reset phase", lambda: self.pomodoro.reset_timer()),
                         ("Skip to next phase", lambda: self.pomodoro.skip_phase())],
            "Tasks": [("New task", self.new_task)],
            "Statistics": [("Export sessions as CSV…", lambda: self.page("Statistics").export_sessions())],
            "Calendar": [("Jump to today", lambda: (self.show_page("Calendar"), self.page("Calendar").go_today()))],
        }
        return menus.get(name)

    def _bind_keys(self) -> None:
        self.bind("<Control-k>", lambda e: self.palette_toggle())
        self.bind("<Control-n>", lambda e: self.new_task())
        for number, name in enumerate(self.PAGE_NAMES, start=1):
            self.bind(f"<Control-Key-{number}>", lambda e, n=name: self.show_page(n))
        for key, handler in (("<space>", lambda: self.pomodoro.toggle()), ("<r>", lambda: self.pomodoro.reset_timer()),
                             ("<s>", lambda: self.pomodoro.skip_phase())):
            self.bind(key, lambda e, h=handler: self._timer_key(h))
        self.bind("<Escape>", lambda e: self.palette.close())

    def _timer_key(self, handler) -> str | None:
        if self.current != "Pomodoro" or isinstance(self.focus_get(), (tk.Entry, tk.Text)):
            return None
        handler()
        return "break"

    # ---------------------------------------------------------------------- pages

    def page(self, name: str):
        if name not in self.pages:
            self.pages[name] = PAGES[name][0](self.content, self)
        return self.pages[name]

    def show_page(self, name: str, animate: bool = True) -> None:
        if name == self.current:
            self.pages[name].on_show()
            return
        if self.current:
            old = self.pages[self.current]
            old.place_forget()
            old.on_hide()
        page = self.page(name)
        self.current = name
        offset = 16 if animate and anim.enabled() else 0
        page.place(x=0, y=offset, relwidth=1, relheight=1)
        page.lift()
        page.on_show()
        if offset:
            anim.tween(page, 0.3, lambda t: page.place_configure(y=round(offset * (1 - t))))
        self.title_text.jump_to(self.PAGE_NAMES.index(name))
        self.dock.set_active(name)

    def change_page(self, name: str) -> None:       # v1 name, kept for compatibility
        self.show_page(name)

    # ------------------------------------------------------------------- services

    def toast(self, message: str, kind: str = "info") -> None:
        self.toaster.show(message, kind)

    def refresh_badges(self) -> None:
        pending = task_service.count_pending()
        self.dock.set_badge("Tasks", pending or None)
        timer = getattr(self, "pomodoro", None)
        self.dock.set_badge("Pomodoro", True if timer and timer.timer.running else None)

    def palette_toggle(self) -> None:
        self.palette.toggle()

    def new_task(self) -> None:
        self.show_page("Tasks")
        self.page("Tasks").focus_new_task()

    def open_task_search(self, text: str) -> None:
        self.show_page("Tasks")
        self.page("Tasks").set_search(text)

    def toggle_timer(self) -> None:
        self.show_page("Pomodoro")
        self.pomodoro.toggle()

    def toggle_theme(self) -> None:
        update_settings(theme="Light" if theme.mode() == "dark" else "Dark")
        self.apply_settings()

    def apply_settings(self) -> None:
        """Re-read preferences and push them to every live component."""
        self.settings = get_settings()
        theme.apply(self.settings["theme"])
        self.configure(fg_color=theme.pair("bg"))
        animations = bool(self.settings["animations"])
        anim.set_enabled(animations)
        self.dock.set_animate(animations)
        self.title_text.set_animate(animations)
        self.theme_button.configure(image=icon("sun" if theme.mode() == "dark" else "moon", 16, "text"))
        self.pomodoro.apply_settings()
        self._start_cursor()

    def _start_cursor(self) -> None:
        want = bool(self.settings["cursor_fx"]) and bool(self.settings["animations"])
        self.cursor.set_enabled(want)

    def _close(self) -> None:
        self.cursor.disable()
        self.destroy()
