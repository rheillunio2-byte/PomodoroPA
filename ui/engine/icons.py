"""A small vector icon set rendered with Pillow.

Icons are described on a 24×24 grid (stroke style, like Lucide/Feather) and
rasterised on demand at any size with 4× supersampling, so they stay crisp on
high-DPI screens and can be tinted for light/dark themes.  This replaces the
emoji the v1 UI used for navigation, which render as tiny monochrome glyphs on
Windows.

Op codes (all coordinates on the 24-unit grid):

    ("l",  [(x, y), ...])            polyline
    ("c",  cx, cy, r)                circle outline
    ("cf", cx, cy, r)                filled circle
    ("r",  x, y, w, h, radius)       rounded-rect outline
    ("rf", x, y, w, h, radius)       rounded-rect fill
    ("p",  [(x, y), ...])            filled polygon with softened corners
    ("a",  cx, cy, r, start, end)    arc, degrees clockwise from 3 o'clock
    ("e",  cx, cy, r)                erase a disc (punches holes)

Any op may end with a dict: ``{"w": 3}`` overrides the stroke width.
"""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw

from ui.engine.colors import hex_to_rgb

GRID = 24
SUPERSAMPLE = 4


def _star(cx: float, cy: float, outer: float, inner: float, points: int = 5):
    pts = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / points
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts


ICONS: dict[str, list[tuple]] = {
    "home": [("l", [(3, 11.5), (12, 3.5), (21, 11.5)]),
             ("l", [(5.5, 10), (5.5, 20.5), (18.5, 20.5), (18.5, 10)]),
             ("l", [(10, 20.5), (10, 14.5), (14, 14.5), (14, 20.5)])],
    "timer": [("c", 12, 13.5, 8), ("l", [(12, 13.5), (12, 9.5)]),
              ("l", [(9.5, 2.5), (14.5, 2.5)]), ("l", [(12, 2.5), (12, 5.5)])],
    "tasks": [("r", 3.5, 3.5, 17, 17, 4.5), ("l", [(8, 12.3), (11, 15.3), (16.3, 9.2)])],
    "stats": [("l", [(5, 20), (5, 13)], {"w": 3}), ("l", [(12, 20), (12, 4)], {"w": 3}),
              ("l", [(19, 20), (19, 9)], {"w": 3})],
    "calendar": [("r", 3, 4.5, 18, 16.5, 4), ("l", [(3, 10), (21, 10)]),
                 ("l", [(8, 2.5), (8, 6.5)]), ("l", [(16, 2.5), (16, 6.5)])],
    "history": [("c", 12, 12, 9), ("l", [(12, 7), (12, 12), (15.5, 14)])],
    "settings": [("l", [(4, 7), (20, 7)]), ("l", [(4, 12), (20, 12)]), ("l", [(4, 17), (20, 17)]),
                 ("e", 9, 7, 3.6), ("c", 9, 7, 2.3), ("e", 15, 12, 3.6), ("c", 15, 12, 2.3),
                 ("e", 8, 17, 3.6), ("c", 8, 17, 2.3)],
    "about": [("c", 12, 12, 9), ("l", [(12, 11), (12, 16.5)]), ("cf", 12, 7.7, 1.25)],
    "play": [("p", [(7.5, 4.5), (19, 12), (7.5, 19.5)])],
    "pause": [("rf", 6, 4.5, 4, 15, 1.4), ("rf", 14, 4.5, 4, 15, 1.4)],
    "reset": [("a", 12, 12, 8.5, -60, 215), ("l", [(3.2, 6.3), (3.8, 11.8), (9.3, 11.2)])],
    "skip": [("p", [(5, 5), (15.5, 12), (5, 19)]), ("l", [(19, 5), (19, 19)])],
    "plus": [("l", [(12, 5), (12, 19)]), ("l", [(5, 12), (19, 12)])],
    "x": [("l", [(6, 6), (18, 18)]), ("l", [(18, 6), (6, 18)])],
    "check": [("l", [(5, 12.5), (10, 17.5), (19, 7)])],
    "trash": [("l", [(4, 6.5), (20, 6.5)]), ("l", [(9, 6.5), (9, 4), (15, 4), (15, 6.5)]),
              ("l", [(6, 6.5), (7, 20.5), (17, 20.5), (18, 6.5)]),
              ("l", [(10, 10.5), (10, 16.5)]), ("l", [(14, 10.5), (14, 16.5)])],
    "edit": [("l", [(4, 20), (4.8, 15.8), (16.2, 4.4), (19.6, 7.8), (8.2, 19.2), (4, 20)]),
             ("l", [(13.8, 6.8), (17.2, 10.2)])],
    "search": [("c", 11, 11, 7), ("l", [(16.2, 16.2), (21, 21)])],
    "flame": [("l", [(12, 3), (15.6, 7.4), (18, 12), (17.4, 16.4), (14.8, 19.8), (12, 21),
                     (9.2, 19.8), (6.6, 16.4), (6.4, 12.6), (8.4, 9.8), (9.8, 12), (12, 3)])],
    "target": [("c", 12, 12, 9), ("c", 12, 12, 5), ("cf", 12, 12, 1.6)],
    "bell": [("l", [(6, 16), (6, 10.5), (6.8, 8), (8.4, 6), (10.6, 4.8), (13.4, 4.8), (15.6, 6),
                    (17.2, 8), (18, 10.5), (18, 16), (19.5, 18), (4.5, 18), (6, 16)]),
             ("l", [(10, 21), (14, 21)])],
    "download": [("l", [(12, 3.5), (12, 15)]), ("l", [(7.5, 10.5), (12, 15), (16.5, 10.5)]),
                 ("l", [(4, 20), (20, 20)])],
    "chevron-left": [("l", [(15, 5), (8, 12), (15, 19)])],
    "chevron-right": [("l", [(9, 5), (16, 12), (9, 19)])],
    "sun": [("c", 12, 12, 4.2)] + [("l", [(12 + 7.2 * math.cos(a), 12 + 7.2 * math.sin(a)),
                                          (12 + 9.6 * math.cos(a), 12 + 9.6 * math.sin(a))])
                                    for a in [i * math.pi / 4 for i in range(8)]],
    "moon": [("cf", 12, 12, 9), ("e", 17, 8, 7.4)],
    "trophy": [("l", [(7, 4), (17, 4), (17, 10), (15.2, 13.2), (12, 14.5), (8.8, 13.2), (7, 10), (7, 4)]),
               ("l", [(7, 6), (3.8, 6), (3.8, 8.2), (6.3, 11.2), (7.6, 11.6)]),
               ("l", [(17, 6), (20.2, 6), (20.2, 8.2), (17.7, 11.2), (16.4, 11.6)]),
               ("l", [(12, 14.5), (12, 18)]), ("l", [(8.5, 20.5), (15.5, 20.5)]),
               ("l", [(9.5, 18), (14.5, 18)])],
    "star": [("p", _star(12, 12.5, 9.5, 4.2))],
    "zap": [("p", [(13, 2.5), (4.8, 13.5), (11, 13.5), (10, 21.5), (19.2, 10), (13, 10)])],
    "medal": [("c", 12, 15, 5.5), ("l", [(8.4, 11.2), (6.4, 3.5), (10, 3.5), (12, 8)]),
              ("l", [(15.6, 11.2), (17.6, 3.5), (14, 3.5), (12, 8)])],
    "coffee": [("l", [(4.5, 9), (4.5, 14.5), (7, 19), (15, 19), (17.5, 14.5), (17.5, 9), (4.5, 9)]),
               ("l", [(17.5, 10), (20, 10), (20, 14), (17.5, 14)]),
               ("l", [(8, 3.5), (8, 6)]), ("l", [(11, 3.5), (11, 6)]), ("l", [(14, 3.5), (14, 6)])],
    "layers": [("l", [(12, 3.5), (21, 8.5), (12, 13.5), (3, 8.5), (12, 3.5)]),
               ("l", [(3, 12.5), (12, 17.5), (21, 12.5)]), ("l", [(3, 16.5), (12, 21.5), (21, 16.5)])],
    "clock": [("c", 12, 12, 9), ("l", [(12, 7), (12, 12), (15.5, 14)])],
    "folder": [("l", [(3, 6.5), (9, 6.5), (11, 9), (21, 9), (21, 19.5), (3, 19.5), (3, 6.5)])],
    "sparkle": [("p", [(12, 3), (14.2, 9.8), (21, 12), (14.2, 14.2), (12, 21), (9.8, 14.2),
                       (3, 12), (9.8, 9.8)])],
    "lock": [("r", 5, 11, 14, 10, 3), ("a", 12, 8, 4, 180, 360), ("l", [(8, 8), (8, 11)]),
             ("l", [(16, 8), (16, 11)])],
    "link": [("l", [(10, 14), (14, 10)]), ("l", [(8.2, 11.8), (5.6, 14.4), (5.6, 18.4), (9.6, 18.4), (12.2, 15.8)]),
             ("l", [(15.8, 12.2), (18.4, 9.6), (18.4, 5.6), (14.4, 5.6), (11.8, 8.2)])],
    "minus": [("l", [(5, 12), (19, 12)])],
}


def available() -> list[str]:
    return sorted(ICONS)


def _stroke_width(options: dict | None, base: float) -> float:
    return options.get("w", base) if options else base


@lru_cache(maxsize=512)
def render_mask(name: str, px: int, stroke: float = 2.0) -> Image.Image:
    """Return the icon as an ``L`` mask of ``px × px`` pixels."""
    if name not in ICONS:
        raise KeyError(f"Unknown icon: {name!r}")
    px = max(4, int(px))
    size = px * SUPERSAMPLE
    unit = size / GRID
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)

    def pt(point):
        return point[0] * unit, point[1] * unit

    def caps(points, width):
        radius = width / 2
        for x, y in points:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)

    for op in ICONS[name]:
        options = op[-1] if isinstance(op[-1], dict) else None
        code = op[0]
        width = _stroke_width(options, stroke) * unit
        if code == "l":
            pts = [pt(p) for p in op[1]]
            draw.line(pts, fill=255, width=round(width), joint="curve")
            caps([pts[0], pts[-1]], width)
        elif code == "c":
            _, cx, cy, r = op[:4]
            draw.ellipse(((cx - r) * unit, (cy - r) * unit, (cx + r) * unit, (cy + r) * unit),
                         outline=255, width=round(width))
        elif code == "cf":
            _, cx, cy, r = op[:4]
            draw.ellipse(((cx - r) * unit, (cy - r) * unit, (cx + r) * unit, (cy + r) * unit), fill=255)
        elif code == "e":
            _, cx, cy, r = op[:4]
            draw.ellipse(((cx - r) * unit, (cy - r) * unit, (cx + r) * unit, (cy + r) * unit), fill=0)
        elif code in ("r", "rf"):
            _, x, y, w, h, radius = op[:6]
            box = (x * unit, y * unit, (x + w) * unit, (y + h) * unit)
            if code == "r":
                draw.rounded_rectangle(box, radius * unit, outline=255, width=round(width))
            else:
                draw.rounded_rectangle(box, radius * unit, fill=255)
        elif code == "p":
            pts = [pt(p) for p in op[1]]
            draw.polygon(pts, fill=255)
            closed = pts + [pts[0]]
            draw.line(closed, fill=255, width=round(width), joint="curve")
            caps(pts, width)
        elif code == "a":
            _, cx, cy, r, start, end = op[:6]
            draw.arc(((cx - r) * unit, (cy - r) * unit, (cx + r) * unit, (cy + r) * unit),
                     start, end, fill=255, width=round(width))
            for angle in (start, end):
                a = math.radians(angle)
                caps([((cx + r * math.cos(a)) * unit, (cy + r * math.sin(a)) * unit)], width)
    return mask.resize((px, px), Image.LANCZOS)


@lru_cache(maxsize=512)
def render_icon(name: str, px: int, color: str = "#ffffff", stroke: float = 2.0) -> Image.Image:
    """Return the icon as a tinted RGBA image of ``px × px`` pixels."""
    mask = render_mask(name, px, stroke)
    image = Image.new("RGBA", mask.size, hex_to_rgb(color) + (0,))
    image.putalpha(mask)
    return image
