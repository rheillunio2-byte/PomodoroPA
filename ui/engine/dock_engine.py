"""Dock physics and layout – a Python port of React Bits' ``<Dock />``.

What is ported, with the same defaults as the component:

* per-icon spring (``mass 0.1, stiffness 150, damping 12``) chasing a target
  size of ``base + (magnification − base) · cos²(π/2 · distance/reach)``
* the panel grows/shrinks with the icons and stays centred
* click "hop" with gravity and decaying bounces (``bounce``)
* separators, ``active`` indicator dots, badges, labels, keyboard focus
* the dock shrinks everything evenly when its parent is too narrow (``fit``)

The engine only deals in numbers; ``dock_render`` turns them into pixels.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

HOP = 0.4            # hop height as a fraction of icon size
HOP_TIME = 0.38      # seconds for one hop
EDGE = 12            # margin from the container edge (px, before scaling)


@dataclass
class DockItem:
    key: str = ""
    label: str = ""
    icon: str = ""
    active: bool = False
    badge: object = None            # int / str, True for a plain dot, None/False for nothing
    on_click: Optional[Callable[[], None]] = None
    menu: Optional[list] = None     # context-menu rows (see widgets/dock.py)
    separator: bool = False

    @property
    def has_badge(self) -> bool:
        return self.badge is not None and self.badge is not False and self.badge != 0


@dataclass
class _Motion:
    size: float
    velocity: float = 0.0
    lift: float = 0.0
    rise: float = 0.0
    launch: float = 0.0
    gravity: float = 0.0
    hopping: bool = False


@dataclass
class Box:
    """Where one item is drawn, in canvas pixels."""
    index: int
    left: float
    top: float
    size: float
    lift: float = 0.0
    separator: bool = False

    @property
    def right(self) -> float:
        return self.left + self.size

    @property
    def center_x(self) -> float:
        return self.left + self.size / 2


class DockEngine:

    def __init__(self, items: Sequence[DockItem], *, base: float = 50, magnification: float = 70,
                 distance: float = 200, panel_height: float = 68, gap: float = 10,
                 mass: float = 0.1, stiffness: float = 150, damping: float = 12,
                 bounce: bool = True, animate: bool = True):
        self.items = list(items)
        self.raw_base = max(16.0, base)
        self.raw_peak = max(self.raw_base, magnification)
        self.raw_thickness = max(self.raw_base, panel_height)
        self.raw_gap = max(0.0, gap)
        self.raw_distance = max(1.0, distance)
        self.mass = max(0.01, mass)
        self.stiffness = max(1.0, stiffness)
        self.damping = max(0.0, damping)
        self.bounce = bounce
        self.animate = animate
        self.fit = 1.0

        self.pointer_x: Optional[float] = None      # canvas x, ``None`` when outside
        self.focus_index: Optional[int] = None      # keyboard focus
        self.center_x = 0.0
        self._motion: dict[int, _Motion] = {}

    # --------------------------------------------------------------- geometry

    @property
    def base(self) -> float:
        return self.raw_base * self.fit

    @property
    def peak(self) -> float:
        return self.raw_peak * self.fit

    @property
    def thickness(self) -> float:
        return self.raw_thickness * self.fit

    @property
    def gap(self) -> float:
        return self.raw_gap * self.fit

    @property
    def distance(self) -> float:
        return self.raw_distance * self.fit

    @property
    def pad(self) -> float:
        """Padding between the panel edge and the icons (vertical and horizontal)."""
        return (self.thickness - self.base) / 2

    def natural_length(self) -> float:
        """Width of the panel at rest, before fitting (px)."""
        spans = sum(1 if it.separator else self.raw_base for it in self.items)
        return spans + self.raw_gap * max(0, len(self.items) - 1) + self.raw_thickness - self.raw_base

    def max_length(self) -> float:
        """Width needed when icons are fully magnified (used to size the canvas)."""
        return self.natural_length() + self.raw_peak - self.raw_base

    def set_available_width(self, width: float) -> None:
        """Shrink everything evenly if *width* can't hold the dock (``fit``)."""
        room = width - EDGE * 2
        length = self.max_length()
        fit = min(1.0, max(0.4, room / length)) if length > 0 else 1.0
        fit = round(fit, 3)
        if fit != self.fit:
            ratio = fit / self.fit
            for state in self._motion.values():
                state.size *= ratio
                state.velocity *= ratio
            self.fit = fit

    def _state(self, index: int) -> _Motion:
        state = self._motion.get(index)
        if state is None:
            state = self._motion[index] = _Motion(size=self.base)
        return state

    def rest_centres(self) -> list[float]:
        """Item centres relative to the dock centre when nothing is magnified."""
        spans = [1.0 if it.separator else self.base for it in self.items]
        cursor = -(sum(spans) + self.gap * max(0, len(spans) - 1)) / 2
        centres = []
        for span in spans:
            centres.append(cursor + span / 2)
            cursor += span + self.gap
        return centres

    # ---------------------------------------------------------------- physics

    def _focus(self, centres: list[float]) -> Optional[float]:
        if self.pointer_x is not None:
            return self.pointer_x - self.center_x
        if self.focus_index is not None and 0 <= self.focus_index < len(centres):
            return centres[self.focus_index]
        return None

    def target_size(self, rest: float, focus: Optional[float]) -> float:
        reach = 1.0 if focus is None else abs(focus - rest) / self.distance
        if reach >= 1.0:
            return self.base
        return self.base + (self.peak - self.base) * math.cos(reach * math.pi / 2) ** 2

    def step(self, dt: float) -> bool:
        """Advance the simulation; returns ``True`` while anything is still moving."""
        dt = min(1 / 30, max(0.001, dt))
        centres = self.rest_centres()
        focus = self._focus(centres)
        steps = max(1, math.ceil(dt * 240))
        h = dt / steps
        k = self.stiffness / self.mass
        c = self.damping / self.mass
        moving = False

        for index, item in enumerate(self.items):
            if item.separator:
                continue
            state = self._state(index)
            target = self.target_size(centres[index], focus) if self.animate else self.base
            if not self.animate:
                state.size, state.velocity = target, 0.0
            else:
                for _ in range(steps):
                    state.velocity = (state.velocity + h * k * (target - state.size)) / (1 + h * c + h * h * k)
                    state.size += state.velocity * h
                    if not state.hopping:
                        continue
                    state.rise -= state.gravity * h
                    state.lift += state.rise * h
                    if state.lift > 0:
                        continue
                    state.lift = 0.0
                    state.rise *= -0.36
                    if state.rise < state.launch * 0.2:
                        state.rise, state.hopping = 0.0, False

            if abs(state.velocity) < 0.01 and abs(target - state.size) < 0.01:
                state.size, state.velocity = target, 0.0
            else:
                moving = True
            moving = moving or state.hopping
        return moving

    def hop(self, index: int) -> None:
        """Make an icon jump (the macOS "launching" bounce)."""
        if not (self.bounce and self.animate) or not 0 <= index < len(self.items):
            return
        state = self._state(index)
        if state.hopping or self.items[index].separator:
            return
        height = state.size * HOP
        state.gravity = 8 * height / (HOP_TIME * HOP_TIME)
        state.launch = state.gravity * HOP_TIME / 2
        state.rise = state.launch
        state.hopping = True

    # ----------------------------------------------------------------- layout

    def sizes(self) -> list[float]:
        return [1.0 if it.separator else self._state(i).size for i, it in enumerate(self.items)]

    def panel_width(self) -> float:
        sizes = self.sizes()
        return sum(sizes) + self.gap * max(0, len(sizes) - 1) + self.pad * 2

    def boxes(self, panel_bottom: float) -> list[Box]:
        """Pixel boxes for every item.  Icons sit on the panel's bottom padding
        and grow upwards, exactly like ``align-items: flex-end`` in the CSS."""
        sizes = self.sizes()
        panel_left = self.center_x - self.panel_width() / 2
        x = panel_left + self.pad
        bottom = panel_bottom - self.pad
        out = []
        for index, (item, size) in enumerate(zip(self.items, sizes)):
            lift = 0.0 if item.separator else self._state(index).lift
            out.append(Box(index, x, bottom - size, size, lift, item.separator))
            x += size + self.gap
        return out

    def hit_test(self, x: float, panel_bottom: float) -> Optional[int]:
        """Index of the (non-separator) item under canvas-x, with half a gap of slack."""
        slack = self.gap / 2
        for box in self.boxes(panel_bottom):
            if box.separator:
                continue
            if box.left - slack <= x <= box.right + slack:
                return box.index
        return None

    def nearest_focusable(self, index: Optional[int], step: int) -> Optional[int]:
        order = [i for i, it in enumerate(self.items) if not it.separator]
        if not order:
            return None
        if index not in order:
            return order[0] if step > 0 else order[-1]
        return order[(order.index(index) + step) % len(order)]
