"""The circular progress ring used by the timer and the daily-goal widget."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from ui.engine.colors import hex_to_rgb, mix


@lru_cache(maxsize=16)
def _gradient_ring(size: int, ss: int, c1: str, c2: str) -> Image.Image:
    """A full conic gradient disc (c1 at 12 o'clock → c2 sweeping clockwise)."""
    big = size * ss
    img = Image.new("RGB", (big, big), c1)
    draw = ImageDraw.Draw(img)
    segments = 180
    box = (0, 0, big - 1, big - 1)
    for i in range(segments):
        a0 = -90 + i * 360 / segments
        draw.pieslice(box, a0 - 0.6, a0 + 360 / segments + 0.6, fill=mix(c1, c2, i / (segments - 1)))
    return img


def render_ring(size: int, progress: float, *, thickness: float, c1: str, c2: str,
                track: str, bg: str, glow: float = 0.0, ss: int = 2) -> Image.Image:
    """Return an RGB image of the ring at ``progress`` (0‥1), ``size × size`` pixels.

    ``glow`` (0‥1) adds a soft halo behind the arc; the timer animates it
    while a session runs.  Drawing at ``ss``× and downsampling gives smooth
    edges and round end-caps.
    """
    progress = max(0.0, min(1.0, progress))
    big = size * ss
    t = max(2, round(thickness * ss))
    inset = t / 2 + size * 0.05 * ss
    box = (inset, inset, big - inset, big - inset)

    img = Image.new("RGB", (big, big), hex_to_rgb(bg))
    draw = ImageDraw.Draw(img)
    draw.ellipse(box, outline=hex_to_rgb(track), width=t)

    if progress > 0.0005:
        mask = Image.new("L", (big, big), 0)
        mdraw = ImageDraw.Draw(mask)
        end_angle = -90 + 360 * progress
        if progress >= 0.9995:
            mdraw.ellipse(box, outline=255, width=t)
        else:
            mdraw.arc(box, -90, end_angle, fill=255, width=t)
            radius = (big - 2 * inset) / 2 - t / 2   # PIL strokes inward from the box
            centre = big / 2
            for angle in (-90, end_angle):
                x = centre + radius * math.cos(math.radians(angle))
                y = centre + radius * math.sin(math.radians(angle))
                mdraw.ellipse((x - t / 2, y - t / 2, x + t / 2, y + t / 2), fill=255)

        if glow > 0:
            small = max(16, big // 6)
            halo = mask.resize((small, small), Image.BILINEAR).filter(ImageFilter.GaussianBlur(small * 0.035))
            halo = halo.resize((big, big), Image.BILINEAR).point(lambda v: int(v * min(1.0, glow) * 0.55))
            tint = Image.new("RGB", (big, big), hex_to_rgb(c2))
            img = Image.composite(tint, img, halo)

        img.paste(_gradient_ring(size, ss, c1, c2), (0, 0), mask)
        if progress < 0.9995:
            # The start cap overhangs into the gradient's wrap-around seam, so
            # paint it in the starting colour explicitly.
            radius = (big - 2 * inset) / 2 - t / 2   # PIL strokes inward from the box
            x, y = big / 2, big / 2 - radius
            ImageDraw.Draw(img).ellipse((x - t / 2, y - t / 2, x + t / 2, y + t / 2), fill=hex_to_rgb(c1))

    return img.resize((size, size), Image.LANCZOS) if ss > 1 else img
