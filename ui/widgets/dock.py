"""``Dock`` – the magnifying navigation dock (port of React Bits' Dock)."""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from PIL import ImageTk

from ui import anim, theme
from ui.engine import palette
from ui.engine.dock_engine import DockEngine, DockItem
from ui.engine.dock_render import render_dock, tokens
from ui.widgets.base import ThemedCanvas


class Dock(ThemedCanvas):
    """Props mirror the component: ``base``, ``magnification``, ``distance``,
    ``panel_height``, ``gap``, ``roundness``, ``bounce`` (+ ``animate`` for the
    user's reduced-motion setting).  Items are :class:`DockItem` objects."""

    BOTTOM = 8

    def __init__(self, parent, items: Sequence[DockItem], *, base=44, magnification=64, distance=170,
                 panel_height=60, gap=10, roundness=0.5, bounce=True, animate=True):
        self.dpi = theme.scale(parent)
        s = self.dpi
        self.engine = DockEngine(items, base=base * s, magnification=magnification * s, distance=distance * s,
                                 panel_height=panel_height * s, gap=gap * s, bounce=bounce, animate=animate)
        self.roundness = roundness
        self.bottom = self.BOTTOM * s
        self.label_zone = 40 * s
        reach = (self.engine.raw_peak - self.engine.raw_base)
        height = int(self.engine.raw_thickness + reach + self.bottom + self.label_zone)
        super().__init__(parent, bg_token="bg", height=height, width=int(self.engine.max_length() + 160 * s))
        self.canvas_h = height
        self.hover: Optional[int] = None
        self.label_index: Optional[int] = None
        self.label_alpha = 0.0
        self.press_index: Optional[int] = None
        self.focus_ring: Optional[int] = None
        self._photo = None
        self._image_item = None
        self._size = (0, 0)
        self.loop = anim.FrameLoop(self, self._step)

        for sequence, handler in (("<Motion>", self._motion), ("<Leave>", self._leave),
                                  ("<ButtonPress-1>", self._press), ("<ButtonRelease-1>", self._release),
                                  ("<Button-3>", self._context), ("<Configure>", self._configure)):
            self.bind(sequence, handler)

    # --------------------------------------------------------------- public API

    def item(self, key: str) -> Optional[DockItem]:
        return next((it for it in self.engine.items if it.key == key), None)

    def set_active(self, key: str) -> None:
        for it in self.engine.items:
            it.active = (it.key == key)
        self._kick()

    def set_badge(self, key: str, badge) -> None:
        it = self.item(key)
        if it is not None and it.badge != badge:
            it.badge = badge
            self._kick()

    def set_animate(self, value: bool) -> None:
        self.engine.animate = bool(value)
        self._kick()

    def activate(self, index: int) -> None:
        item = self.engine.items[index]
        self.engine.hop(index)
        self._kick()
        if item.on_click:
            item.on_click()

    def redraw(self) -> None:
        self._render()

    # ------------------------------------------------------------------- frames

    @property
    def _panel_bottom(self) -> float:
        return self.canvas_h - self.bottom

    def _kick(self) -> None:
        self.loop.interval = anim.FRAME_MS
        self.loop.start()

    def _step(self, dt: float) -> bool:
        moving = self.engine.step(dt)
        target = 1.0 if self.hover is not None else 0.0
        if self.label_alpha != target:
            rate = 9.0 * dt
            self.label_alpha += max(-rate, min(rate, target - self.label_alpha))
            moving = True
            if self.label_alpha <= 0.001 and target == 0:
                self.label_alpha, self.label_index = 0.0, None
        self._render()
        return moving

    def _render(self) -> None:
        width = max(1, self.winfo_width())
        if width <= 1:
            return
        self.engine.center_x = width / 2
        tk_tokens = tokens(palette.PALETTES[theme.mode()], self.roundness)
        image = render_dock(self.engine, tk_tokens, (width, self.canvas_h), self._panel_bottom,
                            hover=self.label_index, label_alpha=self.label_alpha, focus_ring=self.focus_ring)
        if self._photo is None or self._size != image.size:
            self._photo = ImageTk.PhotoImage(image)
            self._size = image.size
            if self._image_item is None:
                self._image_item = self.create_image(0, 0, anchor="nw", image=self._photo)
            else:
                self.itemconfigure(self._image_item, image=self._photo)
        else:
            self._photo.paste(image)

    # ------------------------------------------------------------------- events

    def _configure(self, event) -> None:
        self.engine.set_available_width(event.width)
        self._kick()

    def _inside(self, y: float) -> bool:
        reach = self.engine.peak - self.engine.base
        return y >= self._panel_bottom - self.engine.thickness - reach - 6 * self.dpi

    def _motion(self, event) -> None:
        if not self._inside(event.y):
            return self._leave(event)
        self.engine.pointer_x = event.x
        hit = self.engine.hit_test(event.x, self._panel_bottom)
        if hit != self.hover:
            self.hover = hit
            if hit is not None:
                self.label_index = hit
        self.configure(cursor="hand2" if hit is not None else "")
        self._kick()

    def _leave(self, _event=None) -> None:
        self.engine.pointer_x = None
        self.hover = None
        self.configure(cursor="")
        self._kick()

    def _press(self, event) -> None:
        self.press_index = self.engine.hit_test(event.x, self._panel_bottom)

    def _release(self, event) -> None:
        hit = self.engine.hit_test(event.x, self._panel_bottom)
        if hit is not None and hit == self.press_index:
            self.activate(hit)
        self.press_index = None

    def _context(self, event) -> None:
        hit = self.engine.hit_test(event.x, self._panel_bottom)
        rows = self.engine.items[hit].menu if hit is not None else None
        if not rows:
            return
        menu = tk.Menu(self, tearoff=0, bg=theme.c("surface2"), fg=theme.c("text"),
                       activebackground=theme.c("tomato"), activeforeground=theme.c("on_tomato"),
                       bd=0, relief="flat", font=theme.font(10))
        for row in rows:
            if row is None:
                menu.add_separator()
            else:
                menu.add_command(label=row[0], command=row[1])
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
