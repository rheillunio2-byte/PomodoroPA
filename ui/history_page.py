import customtkinter as ctk

from services.history_service import get_history


class HistoryPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        # ==========================
        # TITLE
        # ==========================

        title = ctk.CTkLabel(
            self,
            text="📜 Session History",
            font=("Segoe UI", 30, "bold")
        )

        title.pack(
            anchor="w",
            padx=25,
            pady=(20,10)
        )

        # ==========================
        # SEARCH BAR
        # ==========================

        self.search = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Search..."
        )

        self.search.pack(
            fill="x",
            padx=25,
            pady=(0,15)
        )

        self.search.bind(
            "<KeyRelease>",
            lambda e: self.load_history()
        )

        self.filter = ctk.CTkComboBox(
            self,
            values=[
                "All Time",
                "Today",
                "This Week",
                "This Month"
            ],
            width=180,
            command=lambda value: self.load_history()
        )

        self.filter.set("All Time")

        self.filter.pack(
            anchor="w",
            padx=25,
            pady=(0,15)
        )

        # ==========================
        # HISTORY LIST
        # ==========================

        self.history_frame = ctk.CTkScrollableFrame(
            self
        )

        self.history_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10
        )

        # ==========================
        # SUMMARY
        # ==========================

        self.summary = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI",16,"bold")
        )

        self.summary.pack(
            anchor="w",
            padx=25,
            pady=(10,20)
        )

        self.load_history()

    def load_history(self):

        for widget in self.history_frame.winfo_children():
            widget.destroy()

        rows = get_history(
            self.filter.get()
        )
        
        keyword = self.search.get().lower()

        total_sessions = 0
        total_minutes = 0

        for completed_at, minutes, session_type in rows:

            if keyword:

                if keyword not in completed_at.lower() \
                and keyword not in session_type.lower():
                    continue

            total_sessions += 1
            total_minutes += minutes

            if session_type == "Work":
                icon = "🍅"

            elif session_type == "Short Break":
                icon = "☕"

            elif session_type == "Long Break":
                icon = "🌙"

            else:
                icon = "📝"

            card = ctk.CTkFrame(
                self.history_frame,
                corner_radius=12
            )

            card.pack(
                fill="x",
                padx=10,
                pady=6
            )

            ctk.CTkLabel(
                card,
                text=f"{icon}  {session_type}",
                font=("Segoe UI", 17, "bold")
            ).pack(
                anchor="w",
                padx=15,
                pady=(10, 3)
            )

            ctk.CTkLabel(
                card,
                text=f"Completed: {completed_at}",
                font=("Segoe UI", 14)
            ).pack(
                anchor="w",
                padx=15
            )

            ctk.CTkLabel(
                card,
                text=f"Duration: {minutes} minutes",
                font=("Segoe UI", 14)
            ).pack(
                anchor="w",
                padx=15,
                pady=(0, 10)
            )

        average = 0

        if total_sessions > 0:
            average = round(total_minutes / total_sessions)

        self.summary.configure(
            text=(
                f"Sessions: {total_sessions}     "
                f"Focus Time: {total_minutes} min     "
                f"Average: {average} min"
            )
        )