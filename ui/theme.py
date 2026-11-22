"""Theme state shared by every widget.

CustomTkinter widgets accept ``(light, dark)`` colour pairs and re-colour
themselves; raw ``tk.Canvas`` widgets don't, so they subscribe here and redraw
when the mode changes.
"""
from __future__ import annotations

import sys
from typing import Callable

import customtkinter as ctk

from ui.engine import palette
from ui.engine.colors import mix

_mode = "dark"
_listeners: list[Callable[[str], None]] = []
_family: str | None = None
_display_family: str | None = None


# ---------------------------------------------------------------- mode / colour

def apply(setting: str = "Dark") -> str:
    """Apply ``Dark`` / ``Light`` / ``System`` and notify canvases.  Returns the resolved mode."""
    global _mode
    ctk.set_appearance_mode(setting)
    _mode = "light" if str(ctk.get_appearance_mode()).lower().startswith("l") else "dark"
    for listener in list(_listeners):
        try:
            listener(_mode)
        except Exception:        # a dead widget must never break a theme switch
            pass
    return _mode


def mode() -> str:
    return _mode


def subscribe(callback: Callable[[str], None]) -> None:
    _listeners.append(callback)


def unsubscribe(callback: Callable[[str], None]) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def c(token: str) -> str:
    """Current hex colour for a palette token."""
    return palette.PALETTES[_mode][token]


def pair(token: str) -> tuple[str, str]:
    """``(light, dark)`` for CustomTkinter."""
    return palette.LIGHT[token], palette.DARK[token]


def tint(token: str, amount: float, base: str = "surface") -> tuple[str, str]:
    """*token* blended over *base* as a ``(light, dark)`` pair."""
    return (mix(palette.LIGHT[base], palette.LIGHT[token], amount),
            mix(palette.DARK[base], palette.DARK[token], amount))


def resolve(value) -> str:
    """Turn a ``(light, dark)`` pair (or plain hex) into the current hex."""
    if isinstance(value, (tuple, list)):
        return value[0] if _mode == "light" else value[1]
    return value


# ------------------------------------------------------------------------ fonts

def init_fonts(root) -> None:
    """Pick the best installed font once a Tk root exists."""
    global _family, _display_family
    from tkinter import font as tkfont
    have = set(tkfont.families(root))
    pick = lambda options: next((f for f in options if f in have), None)   # noqa: E731
    if sys.platform == "win32":
        _family = pick(["Segoe UI Variable Text", "Segoe UI"]) or "Segoe UI"
        _display_family = pick(["Bahnschrift", "Segoe UI Variable Display", "Segoe UI"]) or _family
    elif sys.platform == "darwin":
        _family = pick(["SF Pro Text", "Helvetica Neue"]) or "Helvetica"
        _display_family = _family
    else:
        _family = pick(["Inter", "Cantarell", "Noto Sans", "DejaVu Sans"]) or "TkDefaultFont"
        _display_family = _family


def font(size: int, weight: str = "normal", display: bool = False) -> tuple:
    family = (_display_family if display else _family) or "Segoe UI"
    return (family, size, weight)


def scale(widget) -> float:
    """UI scale factor (1.0 at 96 dpi) for pixel-exact drawing."""
    try:
        return max(1.0, widget.winfo_fpixels("1i") / 96.0)
    except Exception:
        return 1.0
