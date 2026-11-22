"""Shared canvas plumbing."""
from __future__ import annotations

import tkinter as tk

from ui import theme


class ThemedCanvas(tk.Canvas):
    """A canvas whose background follows the theme and which redraws on change."""

    def __init__(self, parent, bg_token: str = "surface", **kwargs):
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, bg=theme.c(bg_token), **kwargs)
        self.bg_token = bg_token
        theme.subscribe(self._theme_changed)
        self.bind("<Destroy>", self._destroyed, add="+")

    def _destroyed(self, event) -> None:
        if event.widget is self:
            theme.unsubscribe(self._theme_changed)

    def _theme_changed(self, mode: str) -> None:
        self.configure(bg=theme.c(self.bg_token))
        self.redraw()

    def redraw(self) -> None:        # overridden by subclasses
        pass


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    """Rounded rectangle as a smoothed polygon (Tk has no native one)."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)
