"""A month calendar drawn on a canvas (replaces the tkcalendar dependency)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, Optional

from ui import anim, theme
from ui.widgets.base import ThemedCanvas, round_rect

RANK_TOKEN = {4: "plum", 3: "danger", 2: "sun", 1: "muted", 0: "leaf"}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class MonthGrid(ThemedCanvas):

    def __init__(self, parent, on_select: Optional[Callable[[date], None]] = None, bg: str = "surface"):
        self.dpi = theme.scale(parent)
        super().__init__(parent, bg_token=bg, height=int(360 * self.dpi))
        today = date.today()
        self.year, self.month = today.year, today.month
        self.selected = today
        self.summary: dict[str, dict] = {}
        self.on_select = on_select
        self.hover: Optional[date] = None
        self.offset = 0.0
        self._tween = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<Button-1>", self._click)

    # --------------------------------------------------------------------- state

    def set_month(self, year: int, month: int, direction: int = 0) -> None:
        self.year, self.month = year, month
        if self._tween:
            self._tween.cancel()
        if direction:
            span = 36 * self.dpi * direction
            self._tween = anim.tween(self, 0.28, lambda t: self._shift(span * (1 - t)))
        else:
            self.redraw()

    def _shift(self, value: float) -> None:
        self.offset = value
        self.redraw()

    def set_summary(self, summary: dict[str, dict]) -> None:
        self.summary = summary
        self.redraw()

    def select(self, day: date) -> None:
        self.selected = day
        self.redraw()

    # ------------------------------------------------------------------ geometry

    def _days(self) -> list[date]:
        first = date(self.year, self.month, 1)
        start = first - timedelta(days=first.weekday())
        return [start + timedelta(days=i) for i in range(42)]

    def _layout(self):
        s = self.dpi
        w, h = max(self.winfo_width(), 70), max(self.winfo_height(), 70)
        head = 26 * s
        return w, h, head, w / 7, (h - head) / 6

    def _day_at(self, x: float, y: float) -> Optional[date]:
        w, h, head, cw, ch = self._layout()
        if y < head:
            return None
        col, row = int(x // cw), int((y - head) // ch)
        return self._days()[row * 7 + col] if 0 <= col < 7 and 0 <= row < 6 else None

    def _motion(self, event) -> None:
        self._set_hover(self._day_at(event.x, event.y))

    def _set_hover(self, day) -> None:
        if day != self.hover:
            self.hover = day
            self.configure(cursor="hand2" if day else "")
            self.redraw()

    def _click(self, event) -> None:
        day = self._day_at(event.x, event.y)
        if day is None:
            return
        if day.month != self.month:
            self.set_month(day.year, day.month, 1 if day > date(self.year, self.month, 1) else -1)
        self.selected = day
        self.redraw()
        if self.on_select:
            self.on_select(day)

    # ------------------------------------------------------------------- drawing

    def redraw(self) -> None:
        self.delete("all")
        s = self.dpi
        w, h, head, cw, ch = self._layout()
        ox = self.offset
        today = date.today()
        for i, name in enumerate(WEEKDAYS):
            self.create_text(ox + cw * (i + 0.5), head / 2, text=name, fill=theme.c("faint"), font=theme.font(9, "bold"))
        for index, day in enumerate(self._days()):
            col, row = index % 7, index // 7
            x1, y1 = ox + col * cw + 3 * s, head + row * ch + 3 * s
            x2, y2 = x1 + cw - 6 * s, y1 + ch - 6 * s
            in_month = day.month == self.month
            is_sel, is_today = day == self.selected, day == today
            if is_sel:
                round_rect(self, x1, y1, x2, y2, 12 * s, fill=theme.c("tomato"), outline="")
            elif day == self.hover:
                round_rect(self, x1, y1, x2, y2, 12 * s, fill=theme.c("surface2"), outline="")
            if is_today and not is_sel:
                round_rect(self, x1, y1, x2, y2, 12 * s, fill="", outline=theme.c("tomato"), width=2)
            if is_sel:
                ink = theme.c("on_tomato")
            else:
                ink = theme.c("text") if in_month else theme.c("faint")
            self.create_text(x1 + 10 * s, y1 + 9 * s, text=str(day.day), anchor="nw", fill=ink,
                             font=theme.font(12, "bold" if (is_today or is_sel) else "normal"))
            info = self.summary.get(day.isoformat())
            if info and in_month:
                n = min(3, info["total"])
                dot = 4 * s
                total_w = n * dot * 2 + (n - 1) * 3 * s
                x = (x1 + x2) / 2 - total_w / 2 + dot
                colour = theme.c(RANK_TOKEN.get(info["rank"], "muted")) if not is_sel else theme.c("on_tomato")
                for k in range(n):
                    self.create_oval(x - dot, y2 - 14 * s - dot, x + dot, y2 - 14 * s + dot, fill=colour, outline="")
                    x += dot * 2 + 3 * s
