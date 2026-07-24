import customtkinter as ctk
import webbrowser


class AboutPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        scroll.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # ==========================
        # Logo
        # ==========================

        ctk.CTkLabel(
            scroll,
            text="🍅",
            font=("Segoe UI Emoji", 72)
        ).pack(
            pady=(10, 5)
        )

        # ==========================
        # App Name
        # ==========================

        ctk.CTkLabel(
            scroll,
            text="FocusFlow",
            font=("Segoe UI", 34, "bold")
        ).pack()

        ctk.CTkLabel(
            scroll,
            text="Version 1.0.0",
            font=("Segoe UI", 16)
        ).pack(
            pady=(0, 20)
        )

        # ==========================
        # Description
        # ==========================

        ctk.CTkLabel(
            scroll,
            text=(
                "FocusFlow is a modern productivity application\n"
                "designed to help students and professionals\n"
                "stay focused using the Pomodoro Technique."
            ),
            justify="center",
            font=("Segoe UI", 17)
        ).pack(
            pady=(0, 25)
        )

        self.create_section(
            scroll,
            "✨ Features",
            [
                "Pomodoro Timer",
                "Task Manager",
                "Statistics Dashboard",
                "Calendar Planner",
                "Session History",
                "AI Productivity Insights",
                "Customizable Settings"
            ]
        )

        self.create_section(
            scroll,
            "🛠 Technologies Used",
            [
                "Python",
                "CustomTkinter",
                "SQLite",
                "Matplotlib",
                "TkCalendar"
            ]
        )

        self.create_section(
            scroll,
            "👨‍💻 Developer",
            [
                "Developed by:",
                "Rheil Evans T. Lunio",
                "Computer Science Student"
            ]
        )

        github = ctk.CTkButton(
            scroll,
            text="🌐 GitHub Repository",
            command=lambda: webbrowser.open(
                "https://github.com/rheillunio2-byte"
            )
        )

        github.pack(
            pady=15
        )

        ctk.CTkLabel(
            scroll,
            text="© 2026 FocusFlow\nMIT License",
            font=("Segoe UI", 14)
        ).pack(
            pady=20
        )

    def create_section(self, parent, title, items):

        frame = ctk.CTkFrame(parent)

        frame.pack(
            fill="x",
            pady=10
        )

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Segoe UI", 22, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 10)
        )

        for item in items:

            ctk.CTkLabel(
                frame,
                text="• " + item,
                font=("Segoe UI", 16)
            ).pack(
                anchor="w",
                padx=30,
                pady=2
            )