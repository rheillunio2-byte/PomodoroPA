"""Locate a TrueType font for Pillow-rendered text.

Tk labels use the OS font directly; this module is only for the parts of the
UI that are drawn with Pillow (dock labels, rotating text).  The search order
prefers Segoe UI on Windows and falls back to common fonts elsewhere, then to
Pillow's built-in scalable font, so rendering never fails.
"""
from __future__ import annotations

from functools import lru_cache

from PIL import ImageFont

_REGULAR = ["segoeui.ttf", "SegoeUI.ttf", "arial.ttf", "Arial.ttf", "Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "DejaVuSans.ttf"]
_SEMIBOLD = ["seguisb.ttf", "SegoeUI-Semibold.ttf"]
_BOLD = ["segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "DejaVuSans-Bold.ttf"]

_WEIGHTS = {"regular": _REGULAR, "semibold": _SEMIBOLD + _BOLD, "bold": _BOLD}


@lru_cache(maxsize=128)
def get_font(size_px: int, weight: str = "bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size_px = max(6, int(size_px))
    for name in _WEIGHTS.get(weight, _BOLD):
        try:
            return ImageFont.truetype(name, size_px)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size_px)      # Pillow >= 10.1
    except TypeError:                                    # pragma: no cover - very old Pillow
        return ImageFont.load_default()


def text_width(text: str, font) -> float:
    return float(font.getlength(text)) if text else 0.0


def font_metrics(font) -> tuple[int, int]:
    """``(ascent, descent)`` in pixels."""
    try:
        return font.getmetrics()
    except Exception:                                    # pragma: no cover
        size = getattr(font, "size", 12)
        return int(size * 0.8), int(size * 0.2)
