"""Native canvas charts (no matplotlib): themed, animated, hover-aware."""
from __future__ import annotations

import math
from datetime import date, timedelta

from ui import anim, theme
from ui.engine.colors import mix
from ui.engine.motion import clamp, ease_out_cubic
from ui.widgets.base import ThemedCanvas, round_rect

SLICE_TOKENS = ("tomato", "leaf", "sky", "sun", "plum")


def nice_ceiling(maximum: float, ticks: int = 4) -> tuple[float, float]:
    """Return ``(step, top)`` so that ``top = step * n`` (n ≤ ticks) covers *maximum*."""
    if maximum <= 0:
        return 1.0, 1.0
    raw = maximum / ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        step = factor * magnitude
        if step * ticks >= maximum:
            top = step * math.ceil(maximum / step)
            return step, top
    return magnitude * 10, magnitude * 10 * ticks   # pragma: no cover


class BarChart(ThemedCanvas):

    def __init__(self, parent, height: int = 230, bg: str = "surface", token: str = "tomato"):
        self.dpi = theme.scale(parent)
        super().__init__(parent, bg_token=bg, height=int(height * self.dpi))
        self.token = token
        self.rows: list[tuple[str, float]] = []
        self.unit = "min"
        self.empty_text = "Nothing to show yet"
        self._p = 1.0
        self._hover: int | None = None
        self._tween = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))

    def set_data(self, rows, unit: str = "min", animate: bool = True) -> None:
        self.rows, self.unit = list(rows), unit
        if self._tween:
            self._tween.cancel()
        self._p = 0.0 if animate else 1.0
        if animate:
            self._tween = anim.tween(self, 0.9, self._set_progress)
        self.redraw()

    def _set_progress(self, t: float) -> None:
        self._p = t
        self.redraw()

    def _geometry(self):
        s = self.dpi
        w, h = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        left, right, top, bottom = 38 * s, 8 * s, 14 * s, 24 * s
        return w, h, left, right, top, bottom

    def _slot(self, x: float):
        w, h, left, right, top, bottom = self._geometry()
        n = max(1, len(self.rows))
        i = int((x - left) / ((w - left - right) / n))
        return i if 0 <= i < len(self.rows) and left <= x <= w - right else None

    def _motion(self, event) -> None:
        self._set_hover(self._slot(event.x))

    def _set_hover(self, index) -> None:
        if index != self._hover:
            self._hover = index
            self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        w, h, left, right, top, bottom = self._geometry()
        s = self.dpi
        plot_h, plot_w = h - top - bottom, w - left - right
        n = len(self.rows)
        maximum = max([v for _, v in self.rows] or [0])
        step, ceiling = nice_ceiling(maximum)
        muted, grid = theme.c("muted"), theme.c("surface3")
        small = theme.font(8)

        for i in range(int(round(ceiling / step)) + 1):
            y = top + plot_h - plot_h * (i * step / ceiling)
            self.create_line(left, y, w - right, y, fill=grid, dash=(2, 4) if i else None)
            label = f"{i * step:g}"
            self.create_text(left - 6 * s, y, text=label, anchor="e", fill=muted, font=small)

        if n == 0 or maximum == 0:
            self.create_text(left + plot_w / 2, top + plot_h / 2, text=self.empty_text, fill=muted,
                             font=theme.font(11))
        if n == 0:
            return

        slot = plot_w / n
        bar_w = min(slot * 0.62, 40 * s)
        base_color, hot = theme.c(self.token), theme.c("tomato_hi" if self.token == "tomato" else self.token)
        labels_every = max(1, math.ceil(n / max(1, plot_w // (34 * s))))
        for i, (label, value) in enumerate(self.rows):
            cx = left + slot * (i + 0.5)
            x1, x2 = cx - bar_w / 2, cx + bar_w / 2
            round_rect(self, x1, top, x2, top + plot_h, 5 * s, fill=theme.c("surface2"), outline="")
            local = clamp(self._p * (1 + n * 0.05) - i * 0.05)
            bar_h = plot_h * (value / ceiling) * ease_out_cubic(local)
            if bar_h >= 1:
                round_rect(self, x1, top + plot_h - max(bar_h, 4 * s), x2, top + plot_h, min(5 * s, bar_h / 2),
                           fill=hot if i == self._hover else base_color, outline="")
            if i % labels_every == 0:
                self.create_text(cx, h - bottom / 2 + 2 * s, text=label, fill=muted, font=small)

        if self._hover is not None:
            label, value = self.rows[self._hover]
            cx = left + slot * (self._hover + 0.5)
            text = f"{label}: {value:g} {self.unit}"
            ty = max(top + 10 * s, top + plot_h - plot_h * (value / ceiling) - 18 * s)
            tx = min(max(cx, left + 50 * s), w - 60 * s)
            box = self.create_text(tx, ty, text=text, fill=theme.c("text"), font=theme.font(9, "bold"))
            x1, y1, x2, y2 = self.bbox(box)
            bg = round_rect(self, x1 - 7 * s, y1 - 4 * s, x2 + 7 * s, y2 + 4 * s, 7 * s,
                            fill=theme.c("surface3"), outline=theme.c("border"))
            self.tag_lower(bg, box)


class DonutChart(ThemedCanvas):

    def __init__(self, parent, height: int = 230, bg: str = "surface"):
        self.dpi = theme.scale(parent)
        super().__init__(parent, bg_token=bg, height=int(height * self.dpi))
        self.rows: list[tuple[str, int]] = []
        self.centre_label = "tasks"
        self._p = 1.0
        self._tween = None
        self.bind("<Configure>", lambda e: self.redraw())

    def set_data(self, rows, centre_label: str = "tasks", animate: bool = True) -> None:
        self.rows, self.centre_label = [r for r in rows if r[1] > 0], centre_label
        if self._tween:
            self._tween.cancel()
        self._p = 0.0 if animate else 1.0
        if animate:
            self._tween = anim.tween(self, 1.0, self._set_progress)
        self.redraw()

    def _set_progress(self, t: float) -> None:
        self._p = t
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        s = self.dpi
        w, h = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        d = min(h - 24 * s, w * 0.5)
        thick = max(12 * s, d * 0.16)
        cx, cy = d / 2 + 16 * s, h / 2
        box = (cx - d / 2 + thick / 2, cy - d / 2 + thick / 2, cx + d / 2 - thick / 2, cy + d / 2 - thick / 2)
        total = sum(v for _, v in self.rows)
        self.create_oval(*box, outline=theme.c("surface2"), width=thick)
        if not total:
            self.create_text(cx, cy, text="No tasks", fill=theme.c("muted"), font=theme.font(11))
            return
        gap = 3.0 if len(self.rows) > 1 else 0.0
        angle = 0.0
        sweep_total = 360 * ease_out_cubic(self._p)
        legend_x = cx + d / 2 + 28 * s
        row_h = 26 * s
        y0 = cy - row_h * len(self.rows) / 2 + row_h / 2
        for i, (label, value) in enumerate(self.rows):
            colour = theme.c(SLICE_TOKENS[i % len(SLICE_TOKENS)])
            extent = value / total * 360
            visible = max(0.0, min(extent, sweep_total - angle))
            if visible > gap + 0.5:
                self.create_arc(*box, start=90 - angle - gap / 2, extent=-(visible - gap), style="arc",
                                outline=colour, width=thick)
            angle += extent
            ly = y0 + i * row_h
            self.create_oval(legend_x, ly - 5 * s, legend_x + 10 * s, ly + 5 * s, fill=colour, outline="")
            self.create_text(legend_x + 18 * s, ly, text=label, anchor="w", fill=theme.c("text"), font=theme.font(10))
            self.create_text(w - 12 * s, ly, text=f"{value}  ({value / total:.0%})", anchor="e",
                             fill=theme.c("muted"), font=theme.font(10))
        self.create_text(cx, cy - 6 * s, text=str(total), fill=theme.c("text"), font=theme.font(22, "bold", display=True))
        self.create_text(cx, cy + 16 * s, text=self.centre_label, fill=theme.c("muted"), font=theme.font(9))


class Heatmap(ThemedCanvas):
    """Focus minutes per day for the last N weeks (Monday-first columns)."""

    def __init__(self, parent, height: int = 170, bg: str = "surface"):
        self.dpi = theme.scale(parent)
        super().__init__(parent, bg_token=bg, height=int(height * self.dpi))
        self.start: date = date.today()
        self.data: dict[str, int] = {}
        self.weeks = 12
        self._p = 1.0
        self._hover: str | None = None
        self._tween = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))

    def set_data(self, start: date, data: dict[str, int], weeks: int = 12, animate: bool = True) -> None:
        self.start, self.data, self.weeks = start, data, weeks
        if self._tween:
            self._tween.cancel()
        self._p = 0.0 if animate else 1.0
        if animate:
            self._tween = anim.tween(self, 1.1, self._set_progress)
        self.redraw()

    def _set_progress(self, t: float) -> None:
        self._p = t
        self.redraw()

    def _cell(self):
        s = self.dpi
        w, h = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        left, top = 34 * s, 22 * s
        size = max(6.0, min((w - left - 8 * s) / self.weeks, (h - top - 6 * s) / 7))
        return left, top, size

    def _day_at(self, x: float, y: float) -> str | None:
        left, top, size = self._cell()
        col, row = int((x - left) // size), int((y - top) // size)
        if 0 <= col < self.weeks and 0 <= row < 7:
            day = self.start + timedelta(days=col * 7 + row)
            return day.isoformat() if day <= date.today() else None
        return None

    def _motion(self, event) -> None:
        self._set_hover(self._day_at(event.x, event.y))

    def _set_hover(self, day) -> None:
        if day != self._hover:
            self._hover = day
            self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        s = self.dpi
        left, top, size = self._cell()
        today = date.today()
        peak = max(self.data.values() or [0])
        empty = theme.c("surface2")
        pad = max(1.5, size * 0.12)
        for i, name in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
            self.create_text(left - 8 * s, top + size * (i + 0.5), text=name, anchor="e",
                             fill=theme.c("faint"), font=theme.font(8))
        last_month = None
        for col in range(self.weeks):
            first = self.start + timedelta(days=col * 7)
            if first.month != last_month:
                last_month = first.month
                self.create_text(left + col * size, top - 11 * s, text=first.strftime("%b"), anchor="w",
                                 fill=theme.c("faint"), font=theme.font(8))
            local = clamp(self._p * (self.weeks + 4) / self.weeks - col / self.weeks * 1.0)
            for row in range(7):
                day = first + timedelta(days=row)
                if day > today:
                    continue
                minutes = self.data.get(day.isoformat(), 0)
                level = 0 if minutes <= 0 or not peak else 0.28 + 0.72 * min(1.0, minutes / peak)
                colour = mix(empty, theme.c("tomato"), level * ease_out_cubic(local))
                x, y = left + col * size, top + row * size
                outline = theme.c("text") if day.isoformat() == self._hover else ""
                round_rect(self, x + pad, y + pad, x + size - pad, y + size - pad, size * 0.22,
                           fill=colour, outline=outline)
        if self._hover:
            day = date.fromisoformat(self._hover)
            minutes = self.data.get(self._hover, 0)
            self.create_text(left + self.weeks * size, top - 11 * s, anchor="e", fill=theme.c("text"),
                             font=theme.font(9, "bold"),
                             text=f"{day.strftime('%a, %b %d')}: {minutes} min" if minutes else
                             f"{day.strftime('%a, %b %d')}: no focus time")
