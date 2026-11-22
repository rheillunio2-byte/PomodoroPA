"""Cursor animation: a trailing comet, a magnetic ring and click ripples.

Tk cannot paint on top of its own widgets, so on Windows the effect lives in a
borderless, colour-keyed overlay window that is

* *owned* by the main window (so it stacks, minimises and closes with it),
* click-through (``WS_EX_TRANSPARENT``) and never activated, and
* verified: if Windows does not confirm the click-through flag the overlay is
  destroyed immediately, so it can never swallow mouse clicks.

On other platforms the effect is unavailable (``CursorFX.supported()`` is
False); the Dock's own cursor-driven magnification still works everywhere.
"""
from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from collections import deque

from ui import anim, theme
from ui.engine.colors import mix

KEY = "#010203"                      # colour that becomes transparent
HAND = {"hand1", "hand2", "pointinghand", "arrow_hand"}
TEXT = {"xterm", "ibeam"}


class CursorFX:

    def __init__(self, root):
        self.root = root
        self.top: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.loop: anim.FrameLoop | None = None
        self.active = False
        self._follow = [0.0, 0.0]
        self._radius = 13.0
        self._target_radius = 13.0
        self._trail: deque = deque(maxlen=14)
        self._ripples: list[dict] = []
        self._pressed = False
        self._frame = 0
        self._last_move = 0.0
        self._last_pos = (-1, -1)
        self._visible = False
        self._kind = "normal"
        self._binds: list[tuple[str, str]] = []

    # --------------------------------------------------------------- lifecycle

    @staticmethod
    def supported() -> bool:
        return sys.platform == "win32"

    def set_enabled(self, enabled: bool) -> bool:
        """Turn the effect on/off.  Returns the resulting state."""
        if enabled and not self.active:
            self.enable()
        elif not enabled and self.active:
            self.disable()
        return self.active

    def enable(self) -> bool:
        if self.active or not self.supported():
            return self.active
        try:
            top = tk.Toplevel(self.root)
            top.withdraw()
            top.overrideredirect(True)
            top.configure(bg=KEY)
            top.attributes("-transparentcolor", KEY)
            top.transient(self.root)
            canvas = tk.Canvas(top, bg=KEY, highlightthickness=0, bd=0)
            canvas.pack(fill="both", expand=True)
            self.top, self.canvas = top, canvas
            self._sync_geometry()
            top.deiconify()
            top.update_idletasks()
            if not self._make_click_through(top):
                raise RuntimeError("click-through not confirmed")
        except Exception:
            self._teardown()
            return False

        self._build_items()
        self._bind()
        self.active = True
        self.loop = anim.FrameLoop(self.root, self._step)
        self.loop.start()
        return True

    def disable(self) -> None:
        self.active = False
        if self.loop:
            self.loop.stop()
        self._teardown()

    def _teardown(self) -> None:
        for sequence, funcid in self._binds:
            try:
                self.root.unbind(sequence, funcid)
            except Exception:
                pass
        self._binds.clear()
        if self.top is not None:
            try:
                self.top.destroy()
            except Exception:
                pass
        self.top = self.canvas = None
        self._ripples.clear()
        self._trail.clear()

    # ----------------------------------------------------------------- windows

    @staticmethod
    def _make_click_through(top: tk.Toplevel) -> bool:
        import ctypes
        user32 = ctypes.windll.user32                                   # type: ignore[attr-defined]
        hwnd = user32.GetAncestor(top.winfo_id(), 2)                    # GA_ROOT
        GWL_EXSTYLE = -20
        LAYERED, TRANSPARENT, TOOLWINDOW, NOACTIVATE = 0x80000, 0x20, 0x80, 0x08000000
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | LAYERED | TRANSPARENT | TOOLWINDOW | NOACTIVATE)
        return bool(user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & TRANSPARENT)

    def _sync_geometry(self, _event=None) -> None:
        if self.top is None:
            return
        r = self.root
        self.top.geometry(f"{max(1, r.winfo_width())}x{max(1, r.winfo_height())}+{r.winfo_rootx()}+{r.winfo_rooty()}")

    def _bind(self) -> None:
        def add(sequence, func):
            self._binds.append((sequence, self.root.bind(sequence, func, add="+")))

        add("<Configure>", lambda e: self._sync_geometry() if e.widget is self.root else None)
        add("<ButtonPress-1>", self._press)
        add("<ButtonRelease-1>", lambda e: setattr(self, "_pressed", False))

    # ------------------------------------------------------------------ drawing

    def _build_items(self) -> None:
        c = self.canvas
        assert c is not None
        self._trail_items = [c.create_oval(0, 0, 0, 0, fill=KEY, outline="", state="hidden") for _ in range(14)]
        self._ring = c.create_oval(0, 0, 0, 0, outline=theme.c("tomato"), width=2, state="hidden")
        self._ripple_items: list[int] = []

    def _press(self, event) -> None:
        self._pressed = True
        if self.canvas is None:
            return
        x, y = event.x_root - self.root.winfo_rootx(), event.y_root - self.root.winfo_rooty()
        item = self.canvas.create_oval(x, y, x, y, outline=theme.c("tomato"), width=3)
        self._ripples.append({"x": x, "y": y, "t": time.perf_counter(), "item": item})
        self.loop and self.loop.start()

    def _pointer_state(self):
        """Pointer position relative to the window, and what kind of widget it is over."""
        px, py = self.root.winfo_pointerxy()
        x, y = px - self.root.winfo_rootx(), py - self.root.winfo_rooty()
        inside = 0 <= x < self.root.winfo_width() and 0 <= y < self.root.winfo_height()
        kind = "normal"
        if inside and self._frame % 3 == 0:
            try:
                widget = self.root.winfo_containing(px, py)
                if widget is None:
                    inside = False
                else:
                    cursor = str(widget.cget("cursor"))
                    kind = "hand" if cursor in HAND else "text" if cursor in TEXT else "normal"
                    self._kind = kind
            except Exception:
                pass
        return x, y, inside, self._kind

    def _step(self, dt: float) -> bool:
        if not self.active or self.canvas is None:
            return False
        self._frame += 1
        c = self.canvas
        x, y, inside, kind = self._pointer_state()
        now = time.perf_counter()
        if (x, y) != self._last_pos:
            self._last_pos, self._last_move = (x, y), now

        # Idle: nothing moving and no ripples -> poll slowly.
        resting = now - self._last_move > 1.2 and not self._ripples
        self.loop.interval = 60 if (resting or not inside) else anim.FRAME_MS

        if not inside:
            if self._visible:
                for item in (*self._trail_items, self._ring):
                    c.itemconfigure(item, state="hidden")
                self._visible = False
            self._tick_ripples(now)
            return True

        if not self._visible:
            self._follow[:] = [x, y]
            self._trail.clear()
            self._visible = True

        k = 1 - math.exp(-dt * 16)                      # frame-rate independent smoothing
        self._follow[0] += (x - self._follow[0]) * k
        self._follow[1] += (y - self._follow[1]) * k
        self._target_radius = 8.0 if self._pressed else 21.0 if kind == "hand" else 6.0 if kind == "text" else 13.0
        self._radius += (self._target_radius - self._radius) * (1 - math.exp(-dt * 18))

        fx, fy, r = self._follow[0], self._follow[1], self._radius
        c.coords(self._ring, fx - r, fy - r, fx + r, fy + r)
        c.itemconfigure(self._ring, state="normal", outline=theme.c("tomato_hi" if kind == "hand" else "tomato"),
                        width=3 if kind == "hand" else 2)

        self._trail.appendleft((fx, fy))
        total = len(self._trail_items)
        for i, item in enumerate(self._trail_items):
            if i + 1 < len(self._trail):
                tx, ty = self._trail[i + 1]
                size = max(0.8, 5.0 * (1 - i / total))
                colour = mix(theme.c("sun"), theme.c("tomato"), i / total)
                c.coords(item, tx - size, ty - size, tx + size, ty + size)
                c.itemconfigure(item, fill=colour, state="normal")
            else:
                c.itemconfigure(item, state="hidden")
        self._tick_ripples(now)
        return True

    def _tick_ripples(self, now: float) -> None:
        if self.canvas is None:
            return
        alive = []
        for rp in self._ripples:
            t = (now - rp["t"]) / 0.5
            if t >= 1:
                self.canvas.delete(rp["item"])
                continue
            radius = 6 + 34 * (1 - (1 - t) ** 3)
            x, y = rp["x"], rp["y"]
            self.canvas.coords(rp["item"], x - radius, y - radius, x + radius, y + radius)
            self.canvas.itemconfigure(rp["item"], width=max(1, round(4 * (1 - t))))
            alive.append(rp)
        self._ripples = alive
