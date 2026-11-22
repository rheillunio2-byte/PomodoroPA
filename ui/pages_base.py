"""Base class for every page."""
from __future__ import annotations

import customtkinter as ctk


class BasePage(ctk.CTkFrame):
    """A page has a ``title`` (shown in the header) and lifecycle hooks.

    ``on_show`` is called every time the page becomes visible – pages reload
    their data and (re)play their entrance animation there.
    """

    title = ""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def on_show(self) -> None:
        pass

    def on_hide(self) -> None:
        pass

    def scroller(self, **kw) -> ctk.CTkScrollableFrame:
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent", **kw)
        frame.pack(fill="both", expand=True)
        return frame
