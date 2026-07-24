import customtkinter as ctk

from tkinter import messagebox
from services.settings_service import (
    save_settings,
    load_settings,
    save_notification_settings,
    load_notification_settings
)

class SettingsPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=("Segoe UI", 32, "bold")
        )

        title.pack(
            anchor="w",
            padx=25,
            pady=(20,15)
        )

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.scroll.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.build_appearance()

        self.build_pomodoro()

        self.build_notifications()

        self.build_data()

        self.build_preferences()

    def build_appearance(self):

        frame = ctk.CTkFrame(self.scroll)

        frame.pack(
            fill="x",
            pady=10
        )

        ctk.CTkLabel(
            frame,
            text="🎨 Appearance",
            font=("Segoe UI",22,"bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,10)
        )

        self.mode = ctk.CTkComboBox(
            frame,
            values=[
                "System",
                "Dark",
                "Light"
            ],
            width=180,
            command=self.change_mode
        )

        self.mode.set("Dark")

        self.mode.pack(
            anchor="w",
            padx=20,
            pady=(0,20)
        )

    def change_mode(self, mode):

        ctk.set_appearance_mode(mode)

    def save_pomodoro_settings(self):

        try:

            work = int(self.work_entry.get())
            short = int(self.short_entry.get())
            long_break = int(self.long_entry.get())
            interval = int(self.interval_entry.get())

        except ValueError:

            messagebox.showerror(
                "Invalid Input",
                "Please enter whole numbers only."
            )

            return

        if work <= 0 or short <= 0 or long_break <= 0 or interval <= 0:

            messagebox.showwarning(
                "Invalid Values",
                "All values must be greater than zero."
            )

            return

        if work > 180 or short > 60 or long_break > 120:

            messagebox.showwarning(
                "Too Large",
                "Please enter realistic Pomodoro durations."
            )

            return

        save_settings(
            work,
            short,
            long_break,
            interval
        )

        messagebox.showinfo(
            "Success",
            "Pomodoro settings saved successfully!"
        )

    def save_notification_preferences(self):

        save_notification_settings(

            self.notification_switch.get(),

            self.sound_switch.get()

        )

        messagebox.showinfo(
            "Success",
            "Notification settings saved."
        )

    def build_pomodoro(self):

        frame = ctk.CTkFrame(self.scroll)

        frame.pack(
            fill="x",
            pady=10
        )

        ctk.CTkLabel(
            frame,
            text="🍅 Pomodoro Settings",
            font=("Segoe UI",22,"bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,15)
        )

        # Work Duration

        ctk.CTkLabel(
            frame,
            text="Work Duration (minutes)"
        ).pack(anchor="w", padx=20)

        self.work_entry = ctk.CTkEntry(frame, width=120)

        self.work_entry.pack(anchor="w", padx=20, pady=(5,10))

        # Short Break

        ctk.CTkLabel(
            frame,
            text="Short Break (minutes)"
        ).pack(anchor="w", padx=20)

        self.short_entry = ctk.CTkEntry(frame, width=120)

        self.short_entry.pack(anchor="w", padx=20, pady=(5,10))

        # Long Break

        ctk.CTkLabel(
            frame,
            text="Long Break (minutes)"
        ).pack(anchor="w", padx=20)

        self.long_entry = ctk.CTkEntry(frame, width=120)

        self.long_entry.pack(anchor="w", padx=20, pady=(5,10))

        # Long Break Every

        ctk.CTkLabel(
            frame,
            text="Long Break Every"
        ).pack(anchor="w", padx=20)

        self.interval_entry = ctk.CTkEntry(frame, width=120)

        self.interval_entry.pack(anchor="w", padx=20, pady=(5,20))

        work, short, long_break, interval = load_settings()

        self.work_entry.insert(0, str(work))

        self.short_entry.insert(0, str(short))

        self.long_entry.insert(0, str(long_break))

        self.interval_entry.insert(0, str(interval))

        ctk.CTkButton(
            frame,
            text="💾 Save Pomodoro Settings",
            command=self.save_pomodoro_settings
        ).pack(
            padx=20,
            pady=(0,20),
            anchor="w"
        )


    def build_notifications(self):

        frame = ctk.CTkFrame(self.scroll)

        frame.pack(
            fill="x",
            pady=10
        )

        ctk.CTkLabel(
            frame,
            text="🔔 Notifications",
            font=("Segoe UI",22,"bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,15)
        )

        notifications, sounds = load_notification_settings()

        self.notification_switch = ctk.CTkSwitch(
            frame,
            text="Enable Desktop Notifications"
        )

        if notifications:
            self.notification_switch.select()

        self.notification_switch.pack(
            anchor="w",
            padx=20,
            pady=8
        )

        self.sound_switch = ctk.CTkSwitch(
            frame,
            text="Enable Sound Effects"
        )

        if sounds:
            self.sound_switch.select()

        self.sound_switch.pack(
            anchor="w",
            padx=20,
            pady=8
        )

        ctk.CTkButton(
            frame,
            text="💾 Save Notification Settings",
            command=self.save_notification_preferences
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,20)
        )


    def build_data(self):
        pass


    def build_preferences(self):
        pass