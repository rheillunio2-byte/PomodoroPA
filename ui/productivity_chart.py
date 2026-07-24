import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ProductivityChart(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        figure = Figure(
            figsize=(7, 3),
            dpi=100
        )

        ax = figure.add_subplot(111)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        hours = [2, 4, 3, 5, 6, 4, 7]

        ax.plot(
            days,
            hours,
            linewidth=3,
            marker="o"
        )

        ax.set_title("Weekly Focus Time")

        ax.set_ylabel("Hours")

        ax.grid(True)

        canvas = FigureCanvasTkAgg(
            figure,
            self
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )