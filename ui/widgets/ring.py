"""Circular progress ring with centre text and a confetti burst."""
from __future__ import annotations

import math
import random

from PIL import ImageTk

from ui import anim, theme
from ui.engine.ring_render import render_ring
from ui.widgets.base import ThemedCanvas

# Timer mode -> (gradient start, gradient end) palette tokens
MODE_GRADIENTS = {"Work": ("tomato_a", "tomato_b"), "Short Break": ("leaf", "sky"), "Long Break": ("sky", "plum")}


class Ring(ThemedCanvas):

    def __init__(self, parent, size: int = 300, thickness: int = 16, bg: str = "bg",
                 main_pt: int = 54, sub_pt: int = 13):
        self.dpi = theme.scale(parent)
        self.px = int(size * self.dpi)
        self.thickness = thickness * self.dpi
        super().__init__(parent, bg_token=bg, width=self.px, height=self.px)
        self.progress = 0.0
        self.glow = 0.0
        self.colors = MODE_GRADIENTS["Work"]
        self._photo = None
        self._shown = None
        self._image_item = self.create_image(0, 0, anchor="nw")
        self._main = self.create_text(self.px / 2, self.px / 2 - 8 * self.dpi, text="", anchor="center",
                                      font=theme.font(main_pt, "bold", display=True), fill=theme.c("text"))
        self._sub = self.create_text(self.px / 2, self.px / 2 + 44 * self.dpi, text="", anchor="center",
                                     font=theme.font(sub_pt), fill=theme.c("muted"))
        self._confetti: list[dict] = []
        self._loop = anim.FrameLoop(self, self._fly)
        self.redraw()

    # ----------------------------------------------------------------------- API

    def set_text(self, main: str, sub: str | None = None) -> None:
        self.itemconfigure(self._main, text=main)
        if sub is not None:
            self.itemconfigure(self._sub, text=sub)

    def set_colors(self, mode_name: str) -> None:
        self.colors = MODE_GRADIENTS.get(mode_name, MODE_GRADIENTS["Work"])
        self.redraw()

    def set_progress(self, progress: float, glow: float = 0.0) -> None:
        progress = max(0.0, min(1.0, progress))
        key = (round(progress, 4), round(glow, 2))
        if key == self._shown:
            return
        self.progress, self.glow = progress, glow
        self.redraw()

    def animate_to(self, progress: float, duration: float = 0.7) -> None:
        start = self.progress
        anim.number_tween(self, start, progress, duration, lambda v: self.set_progress(v, self.glow))

    def redraw(self) -> None:
        self.itemconfigure(self._main, fill=theme.c("text"))
        self.itemconfigure(self._sub, fill=theme.c("muted"))
        c1, c2 = (theme.c(t) for t in self.colors)
        image = render_ring(self.px, self.progress, thickness=self.thickness, c1=c1, c2=c2,
                            track=theme.c("surface3"), bg=theme.c(self.bg_token), glow=self.glow)
        if self._photo is None:
            self._photo = ImageTk.PhotoImage(image)
            self.itemconfigure(self._image_item, image=self._photo)
        else:
            self._photo.paste(image)
        self._shown = (round(self.progress, 4), round(self.glow, 2))
        self.tag_raise(self._main)
        self.tag_raise(self._sub)

    # ------------------------------------------------------------------ confetti

    def burst(self, count: int = 46) -> None:
        if not anim.enabled():
            return
        cx = cy = self.px / 2
        palette = [theme.c(t) for t in ("tomato", "sun", "leaf", "sky", "plum")]
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(120, 330) * self.dpi
            self._confetti.append({
                "x": cx, "y": cy, "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed - 80 * self.dpi,
                "rot": random.uniform(0, math.tau), "spin": random.uniform(-9, 9),
                "w": random.uniform(4, 8) * self.dpi, "h": random.uniform(2, 4) * self.dpi,
                "life": random.uniform(0.9, 1.5), "age": 0.0, "color": random.choice(palette),
                "item": self.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill="", outline=""),
            })
        self._loop.start()

    def _fly(self, dt: float) -> bool:
        dt = min(dt, 0.05)
        alive = []
        for p in self._confetti:
            p["age"] += dt
            if p["age"] >= p["life"]:
                self.delete(p["item"])
                continue
            p["vy"] += 520 * self.dpi * dt
            p["vx"] *= 1 - 1.4 * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["spin"] * dt
            squash = abs(math.cos(p["rot"] * 1.3))
            w, h = p["w"], max(1.0, p["h"] * (0.4 + squash))
            cos, sin = math.cos(p["rot"]), math.sin(p["rot"])
            pts = []
            for ox, oy in ((-w, -h), (w, -h), (w, h), (-w, h)):
                pts += [p["x"] + ox * cos - oy * sin, p["y"] + ox * sin + oy * cos]
            fade = 1 - p["age"] / p["life"]
            self.coords(p["item"], *pts)
            self.itemconfigure(p["item"], fill=p["color"] if fade > 0.25 else theme.c(self.bg_token))
            alive.append(p)
        self._confetti = alive
        return bool(alive)
