"""Colour tokens.

Dark mode is a night-time greenhouse (deep green-black, tomato accent); light
mode is a sage-white market stall.  Colour carries meaning in the app: tomato =
focus, leaf green = short break, sky blue = long break.
"""
from __future__ import annotations

from ui.engine.colors import mix

DARK = {
    "bg": "#0C1310", "surface": "#131C18", "surface2": "#1A2621", "surface3": "#22302A",
    "border": "#2B3B34", "text": "#EDEBE0", "muted": "#94A59B", "faint": "#7D8E84",
    "tomato": "#FF5A43", "tomato_hi": "#FF7A5F", "on_tomato": "#1C0E0A",
    "tomato_a": "#FF8A4C", "tomato_b": "#FF4B3E",                # ring gradient
    "leaf": "#6FD08C", "sun": "#F4C24D", "sky": "#6CB6FF", "plum": "#B78CFF", "danger": "#FF6B7A",
}

LIGHT = {
    "bg": "#EDF2EC", "surface": "#FFFFFF", "surface2": "#E5ECE3", "surface3": "#D8E2D6",
    "border": "#CBD8C9", "text": "#15201B", "muted": "#46564D", "faint": "#5F6D65",
    "tomato": "#BE2E1A", "tomato_hi": "#D13A24", "on_tomato": "#FFFFFF",
    "tomato_a": "#FF7A3D", "tomato_b": "#E5381F",
    "leaf": "#237540", "sun": "#8B5E00", "sky": "#2368AF", "plum": "#754CCD", "danger": "#BC2D41",
}

PALETTES = {"dark": DARK, "light": LIGHT}

# What each timer mode looks like.
MODE_TOKENS = {"Work": "tomato", "Short Break": "leaf", "Long Break": "sky"}


def tint(mode: str, token: str, amount: float, base: str = "surface") -> str:
    """*token* blended over *base* – a flat stand-in for "token at N% opacity"."""
    palette = PALETTES[mode]
    return mix(palette[base], palette[token], amount)
