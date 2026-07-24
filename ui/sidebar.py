import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    def __init__(self, parent, callback):

        super().__init__(
            parent,
            width=250,
            corner_radius=0
        )

        self.callback = callback

        self.buttons = {}

        # Logo

        logo = ctk.CTkLabel(
            self,
            text="⏱ FocusFlow",
            font=("Segoe UI", 26, "bold")
        )

        logo.pack(pady=(30, 40))

        pages = [

            ("Dashboard", "🏠"),

            ("Pomodoro", "⏱"),

            ("Tasks", "✅"),

            ("Statistics", "📊"),

            ("Calendar", "📅"),

            ("History", "🕒"),

            ("Settings", "⚙"),

            ("About", "ℹ")

        ]

        for page, icon in pages:

            button = ctk.CTkButton(

                self,

                text=f"{icon}  {page}",

                anchor="w",

                height=45,

                corner_radius=12,

                command=lambda p=page: self.change_page(p)

            )

            button.pack(

                fill="x",

                padx=15,

                pady=6

            )

            self.buttons[page] = button

        self.highlight("Dashboard")

    def change_page(self, page):

        self.highlight(page)

        self.callback(page)

    def highlight(self, active):

        for page, button in self.buttons.items():

            if page == active:

                button.configure(

                    fg_color="#3B82F6",

                    hover_color="#2563EB"

                )

            else:

                button.configure(

                    fg_color="transparent",

                    hover_color="#2A2A2A"

                )