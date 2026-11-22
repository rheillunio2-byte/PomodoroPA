"""A tiny animation scheduler on top of Tk's ``after``.

* ``tween(widget, duration, update)`` – run ``update(eased_progress)`` each frame
* ``FrameLoop``                      – variable-rate loop for self-driven widgets
* ``set_enabled(False)``             – respects the user's "Animations" setting:
  tweens jump straight to their end state.

All timing uses ``perf_counter`` deltas, so animations take the same wall-clock
time regardless of the machine's frame rate.
"""
from __future__ import annotations

import time
import tkinter as tk
from typing import Callable, Optional

from ui.engine.colors import mix
from ui.engine.motion import ease_out_cubic

FRAME_MS = 15

_enabled = True
_active: list["Tween"] = []
_running = False
_host = None


def set_enabled(value: bool) -> None:
    global _enabled
    _enabled = bool(value)


def enabled() -> bool:
    return _enabled


def init(root) -> None:
    """Give the scheduler a widget to hang its ``after`` loop on."""
    global _host
    _host = root


class Tween:
    def __init__(self, widget, duration, update, ease, delay, on_done):
        self.widget, self.duration, self.update = widget, max(0.001, duration), update
        self.ease, self.delay, self.on_done = ease, delay, on_done
        self.start = time.perf_counter()
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def _step(self, now: float) -> bool:
        """Returns True while still running."""
        if self.cancelled:
            return False
        t = (now - self.start - self.delay) / self.duration
        if t < 0:
            return True
        done = t >= 1.0
        try:
            self.update(1.0 if done else self.ease(t))
        except tk.TclError:                       # widget was destroyed mid-animation
            return False
        if done and self.on_done:
            try:
                self.on_done()
            except tk.TclError:
                pass
        return not done


def tween(widget, duration: float, update: Callable[[float], None], *,
          ease=ease_out_cubic, delay: float = 0.0, on_done: Optional[Callable[[], None]] = None) -> Tween:
    handle = Tween(widget, duration, update, ease, delay, on_done)
    if not _enabled or duration <= 0:
        try:
            update(1.0)
            if on_done:
                on_done()
        except tk.TclError:
            pass
        handle.cancelled = True
        return handle
    _active.append(handle)
    _ensure_running(widget)
    return handle


def _ensure_running(widget) -> None:
    global _running
    if _running:
        return
    _running = True
    (_host or widget).after(FRAME_MS, _tick)


def _tick() -> None:
    global _running
    now = time.perf_counter()
    for handle in list(_active):
        if not handle._step(now):
            if handle in _active:
                _active.remove(handle)
    if _active:
        try:
            (_host or tk._default_root).after(FRAME_MS, _tick)       # type: ignore[union-attr]
        except Exception:
            _running = False
    else:
        _running = False


def color_tween(widget, start: str, end: str, duration: float, setter: Callable[[str], None], **kw) -> Tween:
    return tween(widget, duration, lambda t: setter(mix(start, end, t)), **kw)


def number_tween(widget, start: float, end: float, duration: float, setter: Callable[[float], None], **kw) -> Tween:
    return tween(widget, duration, lambda t: setter(start + (end - start) * t), **kw)


class FrameLoop:
    """Calls ``step(dt)`` every frame until it returns ``False``; restartable."""

    def __init__(self, widget, step: Callable[[float], bool]):
        self.widget, self.step = widget, step
        self.interval = FRAME_MS          # ms; widgets raise it while idle
        self._job = None
        self._last = 0.0

    @property
    def running(self) -> bool:
        return self._job is not None

    def start(self) -> None:
        if self._job is None:
            self._last = time.perf_counter()
            self._job = self.widget.after(self.interval, self._run)

    def stop(self) -> None:
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _run(self) -> None:
        self._job = None
        now = time.perf_counter()
        dt, self._last = now - self._last, now
        try:
            again = self.step(dt)
        except tk.TclError:
            return
        if again:
            self._job = self.widget.after(self.interval, self._run)
