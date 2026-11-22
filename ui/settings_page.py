"""Settings.  Switches apply immediately; timer values are saved with a button."""
from __future__ import annotations

import os
import subprocess
import sys
from tkinter import filedialog, messagebox

import customtkinter as ctk

import config
from services import data_service, export_service
from services.notification_service import is_available, notify
from services.settings_service import get_settings, update_settings
from services.sound_service import play_success
from ui import theme
from ui.pages_base import BasePage
from ui.widgets.components import Button, Card, Stepper, heading, label
from ui.widgets.cursor_fx import CursorFX

SHORTCUTS = [("Ctrl + K", "Command palette"), ("Ctrl + 1 … 8", "Switch page"), ("Ctrl + N", "New task"),
             ("Space", "Start / pause timer"), ("R", "Reset timer phase"), ("S", "Skip to next phase")]


class SettingsPage(BasePage):
    title = "Settings"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        body = self.scroller()
        s = get_settings()

        # ---- appearance -----------------------------------------------------------
        card = self._section(body, "Appearance", "Theme and motion.")
        row = self._row(card, "Theme")
        self.theme_picker = ctk.CTkSegmentedButton(
            row, values=["Dark", "Light", "System"], command=lambda v: self._apply(theme=v), height=34,
            corner_radius=10, font=theme.font(12, "bold"), fg_color=theme.pair("surface2"),
            unselected_color=theme.pair("surface2"), unselected_hover_color=theme.pair("surface3"),
            selected_color=theme.pair("tomato"), selected_hover_color=theme.pair("tomato_hi"),
            text_color=theme.pair("text"))
        self.theme_picker.set(s["theme"])
        self.theme_picker.pack(side="right")
        self.anim_switch = self._switch(card, "Animations", "Dock magnification, text effects and transitions.",
                                        s["animations"], lambda v: self._apply(animations=v))
        supported = CursorFX.supported()
        self.cursor_switch = self._switch(
            card, "Cursor effects", "A glowing trail, magnetic ring and click ripples." if supported
            else "Available on Windows only.", s["cursor_fx"] and supported, lambda v: self._apply(cursor_fx=v))
        if not supported:
            self.cursor_switch.configure(state="disabled")

        # ---- timer ----------------------------------------------------------------
        card = self._section(body, "Timer", "Durations are in minutes. Changes apply to the next phase.")
        self.steppers = {}
        for key, name, low, high, suffix in (("work_minutes", "Focus", 1, 180, " min"), ("short_break", "Short break", 1, 60, " min"),
                                             ("long_break", "Long break", 1, 120, " min"),
                                             ("long_break_every", "Long break after", 1, 30, " sessions"),
                                             ("daily_goal", "Daily goal", 1, 24, " sessions")):
            row = self._row(card, name)
            stepper = Stepper(row, s[key], low, high, suffix)
            stepper.pack(side="right")
            self.steppers[key] = stepper
        self.auto_switch = self._switch(card, "Start the next phase automatically",
                                        "Roll from focus into break (and back) without pressing Start.",
                                        s["auto_start"], lambda v: self._apply(auto_start=v))
        Button(card, "Save timer settings", self.save_timer, kind="primary", width=190).pack(anchor="w", padx=20, pady=(6, 18))

        # ---- notifications --------------------------------------------------------
        card = self._section(body, "Notifications", "Alerts when a session or break ends.")
        self.notify_switch = self._switch(card, "Desktop notifications",
                                          "Shown by your system." if is_available() else
                                          "Install the optional 'plyer' package to enable these.",
                                          s["notifications"], lambda v: self._apply(notifications=v))
        self.sound_switch = self._switch(card, "Sound", "A short chime when a phase ends.", s["sounds"],
                                         lambda v: self._apply(sounds=v))
        tests = ctk.CTkFrame(card, fg_color="transparent")
        tests.pack(anchor="w", padx=20, pady=(4, 18))
        Button(tests, "Test sound", lambda: play_success(force=True), kind="ghost", width=120).pack(side="left")
        Button(tests, "Test notification", lambda: notify("FocusFlow", "This is a test notification.", force=True),
               kind="ghost", width=160).pack(side="left", padx=8)

        # ---- data -----------------------------------------------------------------
        card = self._section(body, "Your data", f"Stored locally in {config.DB_PATH}")
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(anchor="w", padx=20, pady=(0, 18))
        Button(actions, "Export sessions", lambda: self._export(export_service.export_sessions_csv, "focusflow_sessions.csv"),
               kind="ghost", icon_name="download", width=160).pack(side="left")
        Button(actions, "Export tasks", lambda: self._export(export_service.export_tasks_csv, "focusflow_tasks.csv"),
               kind="ghost", icon_name="download", width=140).pack(side="left", padx=8)
        Button(actions, "Open data folder", self.open_folder, kind="ghost", icon_name="folder", width=160).pack(side="left")
        Button(actions, "Reset all data…", self.reset_data, kind="danger", icon_name="trash", width=160).pack(side="left", padx=8)

        # ---- shortcuts ------------------------------------------------------------
        card = self._section(body, "Keyboard shortcuts", "")
        for keys, what in SHORTCUTS:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            label(row, keys, 12, "bold", tone="tomato", anchor="w", width=130).pack(side="left")
            label(row, what, 12, tone="muted", anchor="w").pack(side="left")
        ctk.CTkFrame(card, height=14, fg_color="transparent").pack()

    # ---------------------------------------------------------------- layout helpers

    def _section(self, parent, title: str, hint: str) -> Card:
        card = Card(parent)
        card.pack(fill="x", pady=(0, 14))
        heading(card, title, 16).pack(anchor="w", padx=20, pady=(16, 0))
        if hint:
            label(card, hint, 11, tone="muted", anchor="w", wraplength=760, justify="left").pack(anchor="w", padx=20, pady=(0, 10))
        return card

    def _row(self, card, name: str) -> ctk.CTkFrame:
        """A "label on the left" row; build the control with the returned frame as parent."""
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        label(row, name, 13, anchor="w").pack(side="left")
        return row

    def _switch(self, card, title: str, hint: str, value, command) -> ctk.CTkSwitch:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=6)
        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left")
        label(text, title, 13, anchor="w").pack(anchor="w")
        label(text, hint, 11, tone="muted", anchor="w").pack(anchor="w")
        switch = ctk.CTkSwitch(row, text="", width=46, progress_color=theme.pair("tomato"),
                               fg_color=theme.pair("surface3"), button_color=theme.pair("text"))
        switch.configure(command=lambda: command(switch.get()))
        switch.select() if value else switch.deselect()
        switch.pack(side="right")
        return switch

    # -------------------------------------------------------------------- behaviour

    def _apply(self, **changes) -> None:
        try:
            update_settings(**changes)
        except ValueError as error:
            self.app.toast(str(error), "error")
            return
        self.app.apply_settings()

    def save_timer(self) -> None:
        try:
            update_settings(**{key: stepper.get() for key, stepper in self.steppers.items()})
        except ValueError as error:
            self.app.toast(str(error), "error")
            return
        self.app.apply_settings()
        self.app.toast("Timer settings saved", "success")

    def _export(self, writer, name: str) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")], initialfile=name)
        if path:
            try:
                count = writer(path)
            except OSError as error:
                self.app.toast(f"Couldn't save the file: {error.strerror or error}", "error")
                return
            self.app.toast(f"Exported {count} rows", "success")

    def open_folder(self) -> None:
        folder = data_service.data_folder()
        try:
            if sys.platform == "win32":
                os.startfile(folder)                                    # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except Exception as error:
            self.app.toast(f"Couldn't open the folder: {error}", "error")

    def reset_data(self) -> None:
        if not messagebox.askyesno("Reset all data", "Delete every task and every logged session?\n"
                                   "Your settings are kept. This can't be undone."):
            return
        data_service.reset_all_data()
        self.app.refresh_badges()
        self.app.toast("All tasks and sessions deleted", "info")
