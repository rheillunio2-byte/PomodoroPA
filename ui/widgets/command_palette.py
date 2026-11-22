"""Ctrl+K command palette: jump to pages, run actions, find tasks."""
from __future__ import annotations

import customtkinter as ctk

from ui import anim, theme
from ui.engine.motion import ease_out_cubic
from ui.widgets.components import Card, icon


class CommandPalette(Card):

    def __init__(self, app):
        super().__init__(app, width=540, corner_radius=18, fg_color=theme.pair("surface2"))
        self.app = app
        self.results: list[tuple[str, str, callable]] = []
        self.selected = 0
        self.rows: list[ctk.CTkButton] = []

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(14, 6))
        ctk.CTkLabel(top, text="", image=icon("search", 18, "muted")).pack(side="left", padx=(2, 8))
        self.entry = ctk.CTkEntry(top, placeholder_text="Jump to a page, run an action, or find a task…",
                                  border_width=0, fg_color="transparent", height=36, font=theme.font(13))
        self.entry.pack(side="left", fill="x", expand=True)
        self.list = ctk.CTkFrame(self, fg_color="transparent")
        self.list.pack(fill="x", padx=8, pady=(0, 10))

        self.entry.bind("<KeyRelease>", self._typed)
        self.entry.bind("<Escape>", lambda e: self.close())
        self.entry.bind("<Return>", lambda e: self._run(self.selected))
        self.entry.bind("<Down>", lambda e: self._move(1))
        self.entry.bind("<Up>", lambda e: self._move(-1))
        self.is_open = False

    # --------------------------------------------------------------------- data

    def _candidates(self, query: str):
        from services import task_service
        pages = [(f"Go to {p}", "Pages", (lambda p=p: self.app.show_page(p))) for p in self.app.PAGE_NAMES]
        actions = [
            ("New task", "Action", self.app.new_task),
            ("Start or pause the timer", "Action", self.app.toggle_timer),
            ("Switch light / dark theme", "Action", self.app.toggle_theme),
        ]
        out = [c for c in actions + pages if query in c[0].lower()]
        if query:
            for row in task_service.get_tasks(search=query)[:5]:
                out.append((f"Task: {row[1]}", "Tasks", (lambda q=row[1]: self.app.open_task_search(q))))
        return out[:8]

    def _typed(self, event=None) -> None:
        if event is not None and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self.results = self._candidates(self.entry.get().strip().lower())
        self.selected = 0
        for row in self.rows:
            row.destroy()
        self.rows = []
        for i, (text, kind, _) in enumerate(self.results):
            row = ctk.CTkButton(self.list, text=f"{text}", anchor="w", height=34, corner_radius=10,
                                fg_color="transparent", hover_color=theme.pair("surface3"),
                                text_color=theme.pair("text"), font=theme.font(12),
                                command=lambda i=i: self._run(i))
            row.pack(fill="x", padx=4, pady=1)
            self.rows.append(row)
        self._paint()

    def _paint(self) -> None:
        for i, row in enumerate(self.rows):
            row.configure(fg_color=theme.pair("surface3") if i == self.selected else "transparent")

    def _move(self, step: int) -> str:
        if self.rows:
            self.selected = (self.selected + step) % len(self.rows)
            self._paint()
        return "break"

    def _run(self, index: int) -> None:
        if 0 <= index < len(self.results):
            action = self.results[index][2]
            self.close()
            action()

    # ------------------------------------------------------------------ show/hide

    def toggle(self) -> None:
        self.close() if self.is_open else self.open()

    def open(self) -> None:
        self.is_open = True
        self.entry.delete(0, "end")
        self._typed()
        self.place(relx=0.5, anchor="n", y=40)
        self.lift()
        anim.tween(self, 0.22, lambda t: self.place_configure(y=40 - 14 * (1 - t)), ease=ease_out_cubic)
        self.entry.focus_set()

    def close(self) -> None:
        if self.is_open:
            self.is_open = False
            self.place_forget()
            self.app.focus_set()
