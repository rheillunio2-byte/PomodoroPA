"""Colour helpers (hex strings in, hex strings out)."""
from __future__ import annotations

import re

RGB = tuple[int, int, int]


def hex_to_rgb(value: str) -> RGB:
    value = value.strip().lstrip("#")
    if len(value) in (3, 4):
        value = "".join(c * 2 for c in value[:3])
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb[:3]))


def mix(a: str, b: str, t: float) -> str:
    """Blend colour *a* towards *b* (``t`` = 0 → a, 1 → b)."""
    t = max(0.0, min(1.0, t))
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex([x + (y - x) * t for x, y in zip(ra, rb)])


def parse_color(value) -> RGB | None:
    """Parse ``#rgb``, ``#rrggbb``, ``#rrggbbaa`` or ``rgb()/rgba()``; ``None`` if unknown."""
    text = str(value if value is not None else "").strip()
    if re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", text):
        return hex_to_rgb(text)
    match = re.match(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)", text, re.I)
    if match:
        return tuple(int(float(g)) for g in match.groups())  # type: ignore[return-value]
    return None


def luminance(rgb: RGB) -> float:
    """WCAG relative luminance."""
    def channel(c: int) -> float:
        c = max(0.0, min(1.0, c / 255))
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_text(color) -> str | None:
    """Black or white text for a background (same rule as React Bits' RotatingText)."""
    rgb = parse_color(color)
    if rgb is None:
        return None
    return "#0b0b0c" if luminance(rgb) > 0.3 else "#ffffff"
