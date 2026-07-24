import customtkinter as ctk


class StatCard(ctk.CTkFrame):

    def __init__(self, parent, title, value):

        super().__init__(
            parent,
            corner_radius=15,
            height=130
        )

        self.pack_propagate(False)

        self.title = ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI", 16)
        )

        self.title.pack(pady=(15, 5))

        self.value = ctk.CTkLabel(
            self,
            text=value,
            font=("Segoe UI", 32, "bold")
        )

        self.value.pack()

    def set_value(self, value):

        self.value.configure(text=value)