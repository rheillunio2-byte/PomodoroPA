"""Draw a :class:`DockEngine` state into a single Pillow image.

The whole dock (panel, tiles, icons, dots, badges, tooltip) is composed at 2×
and box-filtered down, so every edge is anti-aliased.  Tile+icon sprites are
cached per (size, state, theme); a frame is a handful of pastes.
"""
from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from ui.engine.colors import hex_to_rgb, mix
from ui.engine.dock_engine import DockEngine
from ui.engine.fonts import get_font, text_width
from ui.engine.icons import render_icon

SS = 2


def tokens(p: dict, roundness: float = 0.5) -> dict:
    """Dock colours derived from a palette (see ``palette.py``)."""
    return {
        "bg": p["bg"], "panel": mix(p["bg"], p["text"], 0.055), "edge": mix(p["bg"], p["text"], 0.14),
        "highlight": mix(p["bg"], p["text"], 0.16),
        "tile_top": p["surface3"], "tile_bottom": p["surface2"], "tile_edge": p["border"],
        "active_top": mix(p["surface3"], p["tomato"], 0.55), "active_bottom": mix(p["surface2"], p["tomato"], 0.38),
        "active_edge": mix(p["border"], p["tomato"], 0.6),
        "ink": p["text"], "active_ink": p["text"],
        "dot": p["tomato"], "separator": p["border"],
        "label_bg": p["surface3"], "label_ink": p["text"], "label_edge": p["border"],
        "badge": p["tomato"], "badge_ink": p["on_tomato"], "focus": p["sky"],
        "roundness": roundness,
    }


@lru_cache(maxsize=600)
def _tile(size2: int, icon: str, active: bool, focused: bool, key: tuple, roundness: float, ink_scale: float) -> Image.Image:
    """A tile with its icon, ``size2`` px wide (already at 2× scale)."""
    t = dict(key)
    top, bottom, edge = (t["active_top"], t["active_bottom"], t["active_edge"]) if active else \
                        (t["tile_top"], t["tile_bottom"], t["tile_edge"])
    grad = Image.linear_gradient("L").resize((size2, size2))
    tile = Image.composite(Image.new("RGB", (size2, size2), hex_to_rgb(bottom)),
                           Image.new("RGB", (size2, size2), hex_to_rgb(top)), grad)
    radius = size2 * roundness * 0.5
    draw = ImageDraw.Draw(tile)
    draw.line((radius, SS, size2 - radius, SS), fill=hex_to_rgb(t["highlight"] if not active else mix(top, "#ffffff", 0.25)), width=SS)
    draw.rounded_rectangle((0, 0, size2 - 1, size2 - 1), radius, outline=hex_to_rgb(edge), width=SS)
    if focused:
        draw.rounded_rectangle((0, 0, size2 - 1, size2 - 1), radius, outline=hex_to_rgb(t["focus"]), width=SS * 2)
    glyph = render_icon(icon, max(4, round(size2 * ink_scale)), t["active_ink"] if active else t["ink"], 2.0)
    tile = tile.convert("RGBA")
    tile.alpha_composite(glyph, ((size2 - glyph.width) // 2, (size2 - glyph.height) // 2))
    mask = Image.new("L", (size2, size2), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size2 - 1, size2 - 1), radius, fill=255)
    tile.putalpha(mask)
    return tile


def render_dock(engine: DockEngine, tk: dict, size: tuple[int, int], panel_bottom: float, *,
                hover: int | None = None, label_alpha: float = 0.0, focus_ring: int | None = None) -> Image.Image:
    width, height = size
    img = Image.new("RGB", (width * SS, height * SS), hex_to_rgb(tk["bg"]))
    draw = ImageDraw.Draw(img)
    key = tuple(sorted((k, v) for k, v in tk.items() if isinstance(v, str)))
    boxes = engine.boxes(panel_bottom)

    # Panel
    pw, th = engine.panel_width(), engine.thickness
    left = engine.center_x - pw / 2
    top = panel_bottom - th
    radius = engine.base * tk["roundness"] * 0.5 + engine.pad
    rect = (left * SS, top * SS, (left + pw) * SS, panel_bottom * SS)
    draw.rounded_rectangle(rect, radius * SS, fill=hex_to_rgb(tk["panel"]), outline=hex_to_rgb(tk["edge"]), width=SS)
    draw.line(((left + radius) * SS, (top + 1) * SS, (left + pw - radius) * SS, (top + 1) * SS),
              fill=hex_to_rgb(tk["highlight"]), width=SS)

    img_rgba = img.convert("RGBA")
    for box in boxes:
        item = engine.items[box.index]
        if box.separator:
            h = engine.base * 0.72
            cy = panel_bottom - th / 2
            draw.line((box.left * SS, (cy - h / 2) * SS, box.left * SS, (cy + h / 2) * SS),
                      fill=hex_to_rgb(tk["separator"]), width=SS)
            continue
        s2 = max(8, round(box.size * SS))
        tile = _tile(s2, item.icon, item.active, focus_ring == box.index, key, tk["roundness"], 0.46)
        y = box.top - box.lift
        img_rgba.paste(tile, (round(box.left * SS), round(y * SS)), tile)

    d = ImageDraw.Draw(img_rgba)
    for box in boxes:
        item = engine.items[box.index]
        if box.separator:
            continue
        y = box.top - box.lift
        if item.active:                                   # indicator dot
            r = 2.2
            cy = panel_bottom - engine.pad / 2
            d.ellipse(((box.center_x - r) * SS, (cy - r) * SS, (box.center_x + r) * SS, (cy + r) * SS),
                      fill=hex_to_rgb(tk["dot"]))
        if item.has_badge:                                # badge
            scale = box.size / engine.base
            bx, by = box.right - 0.04 * box.size, y + 0.04 * box.size
            if item.badge is True:
                r = engine.base * 0.11 * scale
                d.ellipse(((bx - r) * SS, (by - r) * SS, (bx + r) * SS, (by + r) * SS),
                          fill=hex_to_rgb(tk["badge"]), outline=hex_to_rgb(tk["panel"]), width=SS)
            else:
                text = str(item.badge) if str(item.badge).isdigit() and int(item.badge) < 100 else "99+" \
                    if str(item.badge).isdigit() else str(item.badge)
                font = get_font(max(8, round(engine.base * 0.24 * scale * SS)), "bold")
                bh = engine.base * 0.38 * scale * SS
                bw = max(bh, text_width(text, font) + bh * 0.5)
                cx, cy2 = bx * SS, by * SS
                d.rounded_rectangle((cx - bw / 2, cy2 - bh / 2, cx + bw / 2, cy2 + bh / 2), bh / 2,
                                    fill=hex_to_rgb(tk["badge"]), outline=hex_to_rgb(tk["panel"]), width=SS)
                d.text((cx, cy2), text, font=font, fill=hex_to_rgb(tk["badge_ink"]), anchor="mm")

    # Tooltip
    if hover is not None and label_alpha > 0.01 and engine.items[hover].label:
        box = boxes[hover]
        font = get_font(round(max(10, engine.base * 0.26) * SS), "semibold")
        text = engine.items[hover].label
        px, py = engine.base * 0.22 * SS, engine.base * 0.13 * SS
        w, h = text_width(text, font) + px * 2, font.size + py * 2
        layer = Image.new("RGBA", (int(w) + 4, int(h) + 4), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle((1, 1, w + 1, h + 1), h * 0.32, fill=hex_to_rgb(tk["label_bg"]),
                             outline=hex_to_rgb(tk["label_edge"]), width=SS)
        ld.text((1 + w / 2, 1 + h / 2), text, font=font, fill=hex_to_rgb(tk["label_ink"]), anchor="mm")
        a = max(0.0, min(1.0, label_alpha))
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        lx = box.center_x * SS - layer.width / 2
        lx = max(4, min(width * SS - layer.width - 4, lx))
        ly = (box.top - box.lift) * SS - layer.height - 8 * SS + (1 - a) * 6 * SS
        img_rgba.paste(layer, (round(lx), round(ly)), layer)

    return img_rgba.convert("RGB").reduce(SS)
