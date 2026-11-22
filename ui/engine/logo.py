"""The FocusFlow tomato, drawn procedurally (no image assets to ship)."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from ui.engine.colors import hex_to_rgb, mix


@lru_cache(maxsize=16)
def render_logo(px: int, body: str = "#FF5A43", shade: str = "#B8260F", leaf: str = "#6FD08C") -> Image.Image:
    """An RGBA tomato of ``px × px`` pixels with a transparent background."""
    ss = 4
    size = px * ss
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Fruit body: concentric ellipses give a cheap, smooth radial gradient.
    cx, cy = size * 0.5, size * 0.58
    rx, ry = size * 0.43, size * 0.37
    steps = 48
    for i in range(steps):
        t = i / (steps - 1)
        colour = mix(shade, body, min(1.0, t * 1.15))
        shrink = 1 - t * 0.78
        ox = -t * size * 0.07
        oy = -t * size * 0.07
        draw = ImageDraw.Draw(img)
        draw.ellipse((cx + ox - rx * shrink, cy + oy - ry * shrink,
                      cx + ox + rx * shrink, cy + oy + ry * shrink), fill=hex_to_rgb(colour) + (255,))

    # Specular highlight.
    shine = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse((size * 0.22, size * 0.36, size * 0.40, size * 0.50), fill=(255, 255, 255, 110))
    img = Image.alpha_composite(img, shine.filter(ImageFilter.GaussianBlur(size * 0.012)))

    # Calyx: five pointed leaves around the stem.
    draw = ImageDraw.Draw(img)
    leaf_rgb = hex_to_rgb(leaf) + (255,)
    top = (size * 0.5, size * 0.27)
    for i in range(5):
        angle = -math.pi / 2 + (i - 2) * 0.72
        tip = (top[0] + math.cos(angle) * size * 0.27, top[1] + math.sin(angle) * size * 0.19 + size * 0.05)
        left = (top[0] + math.cos(angle - 0.55) * size * 0.08, top[1] + math.sin(angle - 0.55) * size * 0.06)
        right = (top[0] + math.cos(angle + 0.55) * size * 0.08, top[1] + math.sin(angle + 0.55) * size * 0.06)
        draw.polygon([left, tip, right], fill=leaf_rgb)
    draw.ellipse((top[0] - size * 0.06, top[1] - size * 0.045, top[0] + size * 0.06, top[1] + size * 0.045),
                 fill=leaf_rgb)
    draw.rounded_rectangle((size * 0.475, size * 0.12, size * 0.525, size * 0.27), size * 0.025,
                           fill=hex_to_rgb(mix(leaf, "#000000", 0.35)) + (255,))
    return img.resize((px, px), Image.LANCZOS)
