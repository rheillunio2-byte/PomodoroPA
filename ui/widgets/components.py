"""Reusable CustomTkinter building blocks."""
from __future__ import annotations

from functools import lru_cache
from typing import Callable, Optional

import customtkinter as ctk

from ui import anim, theme
from ui.engine.icons import render_icon
from ui.engine.motion import ease_out_back, ease_out_cubic
from ui.engine.palette import DARK, LIGHT


# ------------------------------------------------------------------------ icons

@lru_cache(maxsize=256)
def icon(name: str, size: int = 18, tone: str = "text") -> ctk.CTkImage:
    """A CTkImage that switches tint with the appearance mode and scales with DPI."""
    px = size * 3                                   # render large, CTk scales it down smoothly
    return ctk.CTkImage(light_image=render_icon(name, px, LIGHT[tone]),
                        dark_image=render_icon(name, px, DARK[tone]), size=(size, size))


# ---------------------------------------------------------------------- buttons

_KINDS = {
    #            fill             hover               text          border
    "primary":   ("tomato",       "tomato_hi",        "on_tomato",  None),
    "secondary": ("surface3",     "border",           "text",       None),
    "ghost":     (None,           "surface2",         "text",       "border"),
    "danger":    (None,           "danger",           "text",       "border"),
    "success":   ("leaf",         "leaf",             "on_tomato",  None),
}


class Button(ctk.CTkButton):
    """A button with an eased hover colour, optional icon, and four looks."""

    def __init__(self, parent, text="", command=None, kind="secondary", icon_name: Optional[str] = None,
                 width=None, height=36, **kw):
        if width is None:
            width = 112 if text else 36
        fill, hover, ink, border = _KINDS[kind]
        self.kind = kind
        self._fill = theme.pair(fill) if fill else "transparent"
        self._hover = theme.pair(hover)
        if kind == "danger":
            ink_pair = theme.pair("danger")
        else:
            ink_pair = theme.pair(ink)
        tone = "on_tomato" if kind in ("primary", "success") else ("danger" if kind == "danger" else "text")
        super().__init__(
            parent, text=text, command=command, width=width, height=height, corner_radius=10,
            fg_color=self._fill, hover=False, text_color=ink_pair,
            border_width=1 if border else 0, border_color=theme.pair(border) if border else None,
            font=theme.font(12, "bold"),
            image=icon(icon_name, 16, tone) if icon_name else None, compound="left", **kw)
        self._tween = None
        self._hovering = False
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")

    def _current(self) -> str:
        fill = self._fill if self._fill != "transparent" else theme.pair("surface")
        return theme.resolve(fill)

    def _go(self, target_pair) -> None:
        if self._tween:
            self._tween.cancel()
        start = theme.resolve(self.cget("fg_color")) if self.cget("fg_color") != "transparent" else self._current()
        end = theme.resolve(target_pair)

        def finish():
            self.configure(fg_color=target_pair if not self._hovering or self.kind != "ghost" else self._hover)

        self._tween = anim.color_tween(self, start, end, 0.14, lambda c: self.configure(fg_color=c),
                                       on_done=finish)

    def _enter(self, _e=None) -> None:
        self._hovering = True
        self._go(self._hover)

    def _leave(self, _e=None) -> None:
        self._hovering = False
        self._go(self._fill if self._fill != "transparent" else theme.pair("surface"))
        if self._fill == "transparent":
            self.after(160, lambda: None if self._hovering else self.configure(fg_color="transparent"))


# ------------------------------------------------------------------ cards, text

class Card(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", theme.pair("surface"))
        kw.setdefault("corner_radius", 16)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", theme.pair("border"))
        super().__init__(parent, **kw)


def label(parent, text="", size=12, weight="normal", tone="text", justify=None, **kw) -> ctk.CTkLabel:
    """A text label.  ``justify`` is applied through the inner Tk label because
    CTkLabel's constructor has no such argument (it raises on unknown kwargs)."""
    widget = ctk.CTkLabel(parent, text=text, font=theme.font(size, weight), text_color=theme.pair(tone), **kw)
    inner = getattr(widget, "_label", None)
    if justify and inner is not None:
        inner.configure(justify=justify)
    return widget


def heading(parent, text, size=15) -> ctk.CTkLabel:
    return label(parent, text, size, "bold", anchor="w")


class CountLabel(ctk.CTkLabel):
    """A number that counts up to its new value (shows *what changed*)."""

    def __init__(self, parent, fmt: Callable[[float], str] = lambda v: f"{int(round(v))}",
                 size=30, tone="text", **kw):
        super().__init__(parent, text=fmt(0), font=theme.font(size, "bold", display=True),
                         text_color=theme.pair(tone), **kw)
        self.fmt, self.value, self._tween = fmt, 0.0, None

    def set(self, value: float, animate: bool = True) -> None:
        if self._tween:
            self._tween.cancel()
        start, end = self.value, float(value)
        self.value = end
        if not animate or start == end:
            self.configure(text=self.fmt(end))
            return
        self._tween = anim.number_tween(self, start, end, 0.8, lambda v: self.configure(text=self.fmt(v)))


class Pill(ctk.CTkLabel):
    """A small tinted tag, e.g. a priority or a category."""

    def __init__(self, parent, text, token="muted", **kw):
        super().__init__(parent, text=f"  {text}  ", font=theme.font(10, "bold"), text_color=theme.pair(token),
                         fg_color=theme.tint(token, 0.16), corner_radius=8, height=22, **kw)


def stat_tile(parent, title: str, icon_name: str, token: str, fmt=lambda v: f"{int(round(v))}"):
    """A statistic card: icon chip, big number, caption.  Returns ``(card, CountLabel)``."""
    card = Card(parent)
    chip = ctk.CTkFrame(card, width=38, height=38, corner_radius=12, fg_color=theme.tint(token, 0.18))
    chip.pack(anchor="w", padx=16, pady=(16, 0))
    chip.pack_propagate(False)
    ctk.CTkLabel(chip, text="", image=icon(icon_name, 20, token)).pack(expand=True)
    value = CountLabel(card, fmt=fmt, size=28)
    value.pack(anchor="w", padx=16, pady=(10, 0))
    label(card, title, 11, tone="muted").pack(anchor="w", padx=16, pady=(0, 14))
    return card, value


def empty_state(parent, icon_name: str, title: str, hint: str, action: Optional[tuple] = None) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(frame, text="", image=icon(icon_name, 40, "faint")).pack(pady=(28, 8))
    label(frame, title, 15, "bold").pack()
    label(frame, hint, 12, tone="muted", wraplength=360, justify="center").pack(pady=(4, 12))
    if action:
        Button(frame, action[0], action[1], kind="primary").pack(pady=(0, 24))
    return frame


class Stepper(ctk.CTkFrame):
    """[-]  25  [+]  with validation-free clamping (used on the Settings page)."""

    def __init__(self, parent, value: int, low: int, high: int, suffix: str = "", **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.low, self.high, self.suffix = low, high, suffix
        self.value = value
        Button(self, "", self.dec, kind="ghost", icon_name="minus", width=34, height=34).pack(side="left")
        self.display = ctk.CTkLabel(self, text="", width=78, font=theme.font(14, "bold"))
        self.display.pack(side="left", padx=4)
        Button(self, "", self.inc, kind="ghost", icon_name="plus", width=34, height=34).pack(side="left")
        self._show()

    def _show(self) -> None:
        self.display.configure(text=f"{self.value}{self.suffix}")

    def get(self) -> int:
        return self.value

    def set(self, value: int) -> None:
        self.value = max(self.low, min(self.high, int(value)))
        self._show()

    def inc(self) -> None:
        self.set(self.value + 1)

    def dec(self) -> None:
        self.set(self.value - 1)


# ------------------------------------------------------------------------ toast

class ToastHost:
    """Slide-in confirmation messages (replaces most blocking message boxes)."""

    COLORS = {"info": "sky", "success": "leaf", "error": "danger", "warning": "sun"}
    ICONS = {"info": "about", "success": "check", "error": "x", "warning": "bell"}

    def __init__(self, root, bottom_offset: int = 130):
        self.root, self.bottom, self.current, self._timer = root, bottom_offset, None, None

    def show(self, message: str, kind: str = "info", duration: float = 3.2) -> None:
        if self.current is not None:
            self.current.destroy()
        if self._timer:
            self.root.after_cancel(self._timer)
        token = self.COLORS.get(kind, "sky")
        frame = ctk.CTkFrame(self.root, corner_radius=14, fg_color=theme.pair("surface3"),
                             border_width=1, border_color=theme.tint(token, 0.55, "surface3"))
        chip = ctk.CTkFrame(frame, width=26, height=26, corner_radius=9, fg_color=theme.tint(token, 0.25, "surface3"))
        chip.pack(side="left", padx=(12, 10), pady=12)
        chip.pack_propagate(False)
        ctk.CTkLabel(chip, text="", image=icon(self.ICONS.get(kind, "about"), 14, token)).pack(expand=True)
        label(frame, message, 12, "bold").pack(side="left", padx=(0, 16))
        self.current = frame
        frame.update_idletasks()
        width = frame.winfo_reqwidth()
        frame.place(relx=1.0, x=-24 - width, rely=1.0, y=-self.bottom + 40)
        frame.lift()
        anim.tween(frame, 0.32, lambda t: frame.place_configure(y=-self.bottom + 40 * (1 - t)), ease=ease_out_back)
        self._timer = self.root.after(int(duration * 1000), lambda: self._dismiss(frame))

    def _dismiss(self, frame) -> None:
        if frame is not self.current:
            return

        def finish():
            frame.destroy()
            if self.current is frame:
                self.current = None

        anim.tween(frame, 0.22, lambda t: frame.place_configure(y=-self.bottom + 40 * t),
                   ease=ease_out_cubic, on_done=finish)
