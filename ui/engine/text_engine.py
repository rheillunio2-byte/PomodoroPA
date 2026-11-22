"""RotatingText physics – a Python port of React Bits' ``<RotatingText />``.

Faithful to the component:

* effects ``slide / flip / blur / scale / drop`` with the same poses, springs
  and bezier curves, and ``direction`` up/down
* per-letter stagger (``first / last / center / random / <number>``)
* ``splitBy`` characters / words / lines / custom separator
* ``animatePresenceMode`` ``wait`` (old text leaves, then new enters) or ``sync``
* ``highlight`` block that springs to the width of each new text, with a
  text colour chosen for contrast
* ``next / previous / jump_to / reset``, ``loop``, ``auto``, ``pause`` (hover)
* ``on_next(index)`` callback

Time is in seconds here (the component's ``rotationInterval`` is ms; the
widget converts).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ui.engine.colors import hex_to_rgb, readable_text
from ui.engine.fonts import font_metrics, get_font, text_width
from ui.engine.motion import Spring, resolve_easing

SS = 2
REST = {"y": 0.0, "opacity": 1.0, "scale": 1.0, "rotateX": 0.0}
WIDTH_SPRING = dict(stiffness=320, damping=34)
LAYOUT_SPRING = dict(stiffness=300, damping=25)


def _spring(damping, stiffness, mass=1.0):
    return {"type": "spring", "damping": damping, "stiffness": stiffness, "mass": mass}


def _tween(duration, ease):
    return {"type": "tween", "duration": duration, "ease": ease}


def effect_poses(effect: str, up: bool) -> dict:
    """Same numbers as the component's ``EFFECTS`` table (``y`` is a fraction of line height)."""
    if effect == "flip":
        return dict(initial={"rotateX": -90 if up else 90, "opacity": 0}, exit={"rotateX": 90 if up else -90, "opacity": 0},
                    transition=_tween(0.6, (0.34, 1.4, 0.64, 1)), exit_transition=_tween(0.32, (0.5, 0, 0.75, 0)))
    if effect == "blur":
        return dict(initial={"y": 0.45 if up else -0.45, "opacity": 0}, exit={"y": -0.45 if up else 0.45, "opacity": 0},
                    transition=_tween(0.55, (0.22, 1, 0.36, 1)), exit_transition=None)
    if effect == "scale":
        return dict(initial={"scale": 0.35 if up else 1.7, "opacity": 0}, exit={"scale": 1.7 if up else 0.35, "opacity": 0},
                    transition=_spring(17, 240), exit_transition=None)
    if effect == "drop":
        return dict(initial={"y": -1.1, "opacity": 0}, exit={"y": 1.1, "opacity": 0},
                    transition=_spring(18, 320, 0.9), exit_transition=_tween(0.3, (0.55, 0, 1, 0.45)))
    return dict(initial={"y": 1.0 if up else -1.0, "opacity": 0}, exit={"y": -1.2 if up else 1.2, "opacity": 0},
                transition=_spring(25, 300), exit_transition=None)          # slide (default)


class Track:
    """Progress 0 → 1 driven by a spring or a bezier tween, after a delay."""

    def __init__(self, transition: dict, delay: float = 0.0):
        self.delay = delay
        self.kind = transition.get("type", "spring")
        self.value = 0.0
        if self.kind == "tween":
            self.duration = max(0.001, transition.get("duration", 0.4))
            self.ease = resolve_easing(transition.get("ease"))
            self.elapsed = 0.0
        else:
            self.spring = Spring(0.0, 1.0, stiffness=transition.get("stiffness", 300),
                                 damping=transition.get("damping", 25), mass=transition.get("mass", 1.0),
                                 rest_delta=0.002, rest_speed=0.02)
        self.done = False

    def update(self, dt: float) -> None:
        if self.done:
            return
        if self.delay > 0:
            leftover = dt - self.delay
            self.delay = max(0.0, self.delay - dt)
            if leftover <= 0:
                return
            dt = leftover
        if self.kind == "tween":
            self.elapsed += dt
            t = min(1.0, self.elapsed / self.duration)
            self.value = self.ease(t)
            self.done = t >= 1.0
        else:
            self.value = self.spring.step(dt)
            self.done = self.spring.settled


@dataclass
class Element:
    text: str
    x: float
    y: float
    track: Track = None  # type: ignore[assignment]


@dataclass
class Layer:
    index: int
    text: str
    elements: list[Element]
    width: float
    phase: str = "rest"          # enter | rest | exit

    @property
    def settled(self) -> bool:
        return all(e.track is None or e.track.done for e in self.elements)


class RotatingTextEngine:

    def __init__(self, texts, *, effect="slide", direction="up", highlight=False,
                 highlight_color="#a855f7", rotation_interval=2000, blur=0.0,
                 stagger_duration=0.0, stagger_from="first", split_by="characters",
                 loop=True, auto=True, animate_presence_mode="wait", animate_presence_initial=False,
                 font_px=28, weight="bold", text_color="#ffffff", bg="#000000",
                 overflow_hidden=True, transition=None, animate=True, on_next: Optional[Callable[[int], None]] = None):
        self.texts = list(texts) or [""]
        self.effect = effect
        self.direction = direction
        self.highlight = highlight
        self.highlight_color = highlight_color
        self.interval = rotation_interval / 1000.0
        self.blur = blur
        self.stagger = stagger_duration
        self.stagger_from = stagger_from
        self.split_by = split_by
        self.loop = loop
        self.auto = auto
        self.mode = animate_presence_mode
        self.initial_anim = animate_presence_initial
        self.font_px = font_px
        self.weight = weight
        self.text_color = text_color
        self.bg = bg
        self.overflow_hidden = overflow_hidden
        self.transition = transition
        self.animate = animate
        self.on_next = on_next
        self.paused = False

        self.font = get_font(font_px * SS, weight)
        asc, desc = font_metrics(self.font)
        self.line_h = (asc + desc) / SS
        self.index = 0
        self._since_change = 0.0
        self._pending: Optional[int] = None
        self.layers: list[Layer] = []
        self._poses = effect_poses(effect, direction != "down")
        self._rows = max(len(t.split("\n")) for t in self.texts) if split_by == "lines" else 1
        self.layers.append(self._make_layer(0, enter=self.initial_anim and animate))
        self.width = Spring(self._target_width(), stiffness=WIDTH_SPRING["stiffness"] if highlight else LAYOUT_SPRING["stiffness"],
                            damping=WIDTH_SPRING["damping"] if highlight else LAYOUT_SPRING["damping"],
                            rest_delta=0.05, rest_speed=0.5)

    # ---------------------------------------------------------------- layout

    @property
    def pad_x(self) -> float:
        return 0.28 * self.font_px if self.highlight else 0.0

    @property
    def pad_y(self) -> float:
        return 0.1 * self.font_px if self.highlight else 0.0

    def height(self) -> int:
        return int(math.ceil(self.line_h * self._rows + 2 * self.pad_y))

    def _measure(self, s: str) -> float:
        return text_width(s, self.font) / SS

    def _split(self, text: str) -> list[tuple[list[str], bool]]:
        sb = self.split_by
        if sb == "characters":
            words = text.split(" ")
            return [(list(w), i != len(words) - 1) for i, w in enumerate(words)]
        sep = " " if sb == "words" else "\n" if sb == "lines" else sb
        parts = text.split(sep)
        return [([p], i != len(parts) - 1) for i, p in enumerate(parts)]

    def _make_layer(self, index: int, enter: bool) -> Layer:
        text = self.texts[index]
        groups = self._split(text)
        elements, x, y = [], 0.0, 0.0
        space = self._measure(" ") if self.split_by != "lines" else 0.0
        for chars, needs_space in groups:
            for ch in chars:
                w = self._measure(ch)
                elements.append(Element(ch, x, y))
                if self.split_by != "lines":
                    x += w
            if self.split_by == "lines":
                y += self.line_h
            elif needs_space:
                x += space if self.split_by in ("characters", "words") else self._measure(self.split_by)
        width = max([e.x + self._measure(e.text) for e in elements] or [0.0])
        layer = Layer(index, text, elements, width, "rest")
        if enter:
            self._start(layer, "enter")
        return layer

    def _delay(self, i: int, total: int, shuffled: list[int]) -> float:
        f = self.stagger_from
        if f == "first":
            n = i
        elif f == "last":
            n = total - 1 - i
        elif f == "center":
            n = abs(total // 2 - i)
        elif f == "random":
            n = shuffled[i]
        else:
            n = abs(float(f) - i)
        return n * self.stagger

    def _start(self, layer: Layer, phase: str) -> None:
        layer.phase = phase
        total = len(layer.elements)
        shuffled = random.sample(range(total), total)
        if phase == "enter":
            tr = self.transition or self._poses["transition"]
        else:
            tr = self.transition or self._poses["exit_transition"] or self._poses["transition"]
        for i, el in enumerate(layer.elements):
            el.track = Track(tr, self._delay(i, total, shuffled)) if self.animate else None

    def _target_width(self) -> float:
        layer = next((l for l in reversed(self.layers) if l.phase != "exit"), self.layers[-1])
        return layer.width + 2 * self.pad_x

    # ------------------------------------------------------------- navigation

    def go_to(self, index: int, notify: bool = True) -> None:
        index = max(0, min(index, len(self.texts) - 1))
        if index == self.index and self._pending is None:
            return
        self.index = index
        self._since_change = 0.0
        if notify and self.on_next:
            self.on_next(index)
        if not self.animate:
            self.layers = [self._make_layer(index, enter=False)]
            self.width.snap(self._target_width())
            return
        for layer in self.layers:
            if layer.phase != "exit":
                self._start(layer, "exit")
        if self.mode == "sync":
            self.layers.append(self._make_layer(index, enter=True))
            self.width.target = self._target_width()
        else:
            self._pending = index

    def next(self) -> None:
        cur = self.index
        last = len(self.texts) - 1
        self.go_to(cur + 1 if cur < last else 0 if self.loop else cur)

    def previous(self) -> None:
        cur = self.index
        last = len(self.texts) - 1
        self.go_to(cur - 1 if cur > 0 else last if self.loop else cur)

    def jump_to(self, index: int) -> None:
        self.go_to(index)

    def reset(self) -> None:
        self.go_to(0)

    def set_texts(self, texts) -> None:
        self.texts = list(texts) or [""]
        self.index = min(self.index, len(self.texts) - 1)
        self.layers = [self._make_layer(self.index, enter=False)]
        self.width.snap(self._target_width())

    # ------------------------------------------------------------------- time

    def update(self, dt: float) -> bool:
        """Advance; returns ``True`` while something is animating."""
        dt = min(dt, 0.1)
        busy = False
        for layer in self.layers:
            for el in layer.elements:
                if el.track:
                    el.track.update(dt)
            if layer.phase == "enter" and layer.settled:
                layer.phase = "rest"
            busy = busy or layer.phase != "rest"

        survivors = [l for l in self.layers if not (l.phase == "exit" and l.settled)]
        if len(survivors) != len(self.layers):
            self.layers = survivors
        if self._pending is not None and not any(l.phase == "exit" for l in self.layers):
            self.layers.append(self._make_layer(self._pending, enter=True))
            self._pending = None
            self.width.target = self._target_width()
        elif self._pending is None:
            self.width.target = self._target_width()
        if not self.animate:
            self.width.snap(self.width.target)
        if not self.width.settled:
            self.width.step(dt)
            busy = True

        if self.auto and not self.paused and len(self.texts) > 1:
            self._since_change += dt
            if self._since_change >= self.interval:
                self.next()
                busy = True
        return busy or self._pending is not None

    def idle_ok(self) -> bool:
        """True when nothing animates and nothing needs redrawing."""
        return self._pending is None and all(l.phase == "rest" for l in self.layers) and self.width.settled

    # ----------------------------------------------------------------- render

    @property
    def fg(self) -> str:
        if self.highlight:
            return readable_text(self.highlight_color) or self.text_color
        return self.text_color

    def size(self) -> tuple[int, int]:
        return max(1, int(math.ceil(self.width.value))), self.height()

    def _pose(self, layer: Layer, el: Element) -> dict:
        pose = dict(REST)
        tr = el.track
        if layer.phase == "rest" or tr is None:
            return pose
        p = tr.value
        src, dst = (self._enter_state(), REST) if layer.phase == "enter" else (REST, self._exit_state())
        for k in pose:
            pose[k] = src.get(k, REST[k]) + (dst.get(k, REST[k]) - src.get(k, REST[k])) * p
        pose["opacity"] = max(0.0, min(1.0, pose["opacity"]))
        return pose

    def _enter_state(self):
        return self._poses["initial"]

    def _exit_state(self):
        return self._poses["exit"]

    @staticmethod
    def _sprite(text: str, font_id: tuple, font) -> Image.Image:
        asc, desc = font_metrics(font)
        w = int(math.ceil(text_width(text, font))) + 2
        mask = Image.new("L", (max(2, w), asc + desc), 0)
        ImageDraw.Draw(mask).text((1, 0), text, font=font, fill=255, anchor="la")
        return mask

    def render(self) -> Image.Image:
        w, h = self.size()
        W, H = w * SS, h * SS
        frame = Image.new("RGB", (W, H), hex_to_rgb(self.bg))
        fg = hex_to_rgb(self.fg)
        margin = 0 if (self.highlight or self.overflow_hidden) else int(self.line_h * SS)
        content = Image.new("RGBA", (W, H + 2 * margin), fg + (0,))
        blur_px = self.blur if self.blur > 0 else (10.0 if self.effect == "blur" else 0.0)

        for layer in self.layers:
            ox = (w - layer.width) / 2 if self.highlight else 0.0
            for el in layer.elements:
                if not el.text.strip():
                    continue
                pose = self._pose(layer, el)
                if pose["opacity"] <= 0.003:
                    continue
                sprite = self._sprite(el.text, (el.text, self.font_px, self.weight), self.font)
                sw, sh = sprite.size
                sx, sy = pose["scale"], pose["scale"]
                yoff = pose["y"] * self.line_h * SS
                theta = pose["rotateX"]
                if theta:
                    if abs(theta) >= 90:
                        continue
                    sy *= math.cos(math.radians(theta))
                    yoff += -0.45 * self.font_px * SS * math.sin(math.radians(theta))
                if sx != 1 or sy != 1:
                    nw, nh = max(1, round(sw * sx)), max(1, round(sh * max(sy, 0.02)))
                    sprite = sprite.resize((nw, nh), Image.BICUBIC)
                    dx, dy = (sw - nw) / 2, (sh - nh) / 2
                else:
                    dx = dy = 0.0
                if blur_px > 0 and (layer.phase != "rest"):
                    amount = blur_px * SS * (1 - pose["opacity"] * 0.0)
                    strength = 1 - pose["opacity"]
                    sigma = max(0.0, amount * strength * 0.5)
                    if sigma > 0.4:
                        pad = int(sigma * 3)
                        padded = Image.new("L", (sprite.width + 2 * pad, sprite.height + 2 * pad), 0)
                        padded.paste(sprite, (pad, pad))
                        sprite = padded.filter(ImageFilter.GaussianBlur(sigma))
                        dx -= pad
                        dy -= pad
                alpha = sprite.point(lambda v, a=pose["opacity"]: int(v * a))
                tile = Image.new("RGBA", sprite.size, fg + (0,))
                tile.putalpha(alpha)
                px = round((ox + self.pad_x + el.x) * SS + dx - 1)
                py = round((el.y + self.pad_y) * SS + yoff + dy + margin)
                content.paste(tile, (px, py), tile)

        if self.highlight:
            block = Image.new("L", (W, H), 0)
            ImageDraw.Draw(block).rounded_rectangle((0, 0, W - 1, H - 1), 0.16 * self.font_px * SS, fill=255)
            ImageDraw.Draw(frame).rounded_rectangle((0, 0, W - 1, H - 1), 0.16 * self.font_px * SS,
                                                    fill=hex_to_rgb(self.highlight_color))
            content.putalpha(ImageChops.multiply(content.getchannel("A"), block))
        frame.paste(content.crop((0, margin, W, margin + H)), (0, 0), content.crop((0, margin, W, margin + H)))
        return frame.reduce(SS)
