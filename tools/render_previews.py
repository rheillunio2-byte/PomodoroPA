"""Render component previews (no display needed):  python tools/render_previews.py

Output goes to docs/previews/.  These images come straight from the same engine
code the app runs (Pillow frames), so they show exactly what the widgets blit.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from ui.engine import icons, palette  # noqa: E402
from ui.engine.colors import hex_to_rgb  # noqa: E402
from ui.engine.dock_engine import DockEngine, DockItem  # noqa: E402
from ui.engine.dock_render import render_dock, tokens  # noqa: E402
from ui.engine.fonts import get_font  # noqa: E402
from ui.engine.logo import render_logo  # noqa: E402
from ui.engine.ring_render import render_ring  # noqa: E402
from ui.engine.text_engine import RotatingTextEngine  # noqa: E402

OUT = ROOT / "docs" / "previews"
OUT.mkdir(parents=True, exist_ok=True)
NAV = [("home", "Dashboard"), ("timer", "Pomodoro"), ("tasks", "Tasks"), ("stats", "Statistics"),
       ("calendar", "Calendar"), ("history", "History"), None, ("settings", "Settings"), ("about", "About")]


def dock(mode: str) -> Image.Image:
    p = palette.PALETTES[mode]
    items = [DockItem(separator=True) if n is None else DockItem(key=n[1], icon=n[0], label=n[1]) for n in NAV]
    items[0].active, items[1].badge, items[2].badge = True, True, 5
    e = DockEngine(items, base=44, magnification=64, distance=170, panel_height=60, gap=10)
    width, height = int(e.max_length() + 160), 118
    e.center_x, bottom = width / 2, height - 8
    e.pointer_x = width / 2 - 20
    for _ in range(120):
        e.step(1 / 60)
    return render_dock(e, tokens(p), (width, height), bottom, hover=e.hit_test(e.pointer_x, bottom), label_alpha=1)


def rotating(mode: str) -> Image.Image:
    p = palette.PALETTES[mode]
    rows = []
    for effect, highlight in (("slide", True), ("flip", False), ("blur", False), ("scale", False), ("drop", True)):
        e = RotatingTextEngine(["Focused", "Productive"], effect=effect, highlight=highlight,
                               highlight_color=p["tomato"], stagger_duration=0.025, stagger_from="last",
                               font_px=34, text_color=p["text"], bg=p["bg"], auto=False)
        e.update(0.01)
        e.next()
        frames, t = [], 0
        for step in range(48):
            e.update(1 / 60)
            if step in (3, 9, 15, 21, 30, 47):
                frames.append(e.render())
        for _ in range(90):
            e.update(1 / 60)
        frames.append(e.render())
        rows.append((effect, frames))
    label = get_font(14, "regular")
    gap, lw = 14, 70
    width = lw + max(sum(f.width + gap for f in fr) for _, fr in rows) + gap
    height = sum(max(f.height for f in fr) + gap for _, fr in rows) + gap
    img = Image.new("RGB", (width, height), hex_to_rgb(p["bg"]))
    d, y = ImageDraw.Draw(img), gap
    for effect, frames in rows:
        d.text((gap, y + 10), effect, font=label, fill=hex_to_rgb(p["muted"]))
        x = lw
        for f in frames:
            img.paste(f, (x, y))
            x += f.width + gap
        y += max(f.height for f in frames) + gap
    return img


def rings(mode: str) -> Image.Image:
    p = palette.PALETTES[mode]
    modes = [("Work", "tomato_a", "tomato_b", 0.62), ("Short Break", "leaf", "sky", 0.35), ("Long Break", "sky", "plum", 0.85)]
    img = Image.new("RGB", (3 * 250 + 40, 270), hex_to_rgb(p["bg"]))
    for i, (_, a, b, prog) in enumerate(modes):
        img.paste(render_ring(230, prog, thickness=15, c1=p[a], c2=p[b], track=p["surface3"], bg=p["bg"], glow=0.8),
                  (20 + i * 250, 20))
    return img


def icon_sheet(mode: str) -> Image.Image:
    p = palette.PALETTES[mode]
    names, cols, cell = icons.available(), 10, 70
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell, rows * cell), hex_to_rgb(p["bg"]))
    for i, name in enumerate(names):
        glyph = icons.render_icon(name, 32, p["text"])
        img.paste(glyph, ((i % cols) * cell + 19, (i // cols) * cell + 19), glyph)
    return img


if __name__ == "__main__":
    for mode in ("dark", "light"):
        dock(mode).save(OUT / f"dock-{mode}.png")
        rotating(mode).save(OUT / f"rotating-text-{mode}.png")
        rings(mode).save(OUT / f"timer-rings-{mode}.png")
        icon_sheet(mode).save(OUT / f"icons-{mode}.png")
    logo = render_logo(256)
    logo.save(OUT / "logo.png")
    print("wrote", ", ".join(sorted(p.name for p in OUT.iterdir())))
