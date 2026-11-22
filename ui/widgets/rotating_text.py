"""``RotatingText`` – animated, letter-by-letter text (port of React Bits' RotatingText)."""
from __future__ import annotations

from PIL import ImageTk

from ui import anim, theme
from ui.engine.text_engine import RotatingTextEngine
from ui.widgets.base import ThemedCanvas


class RotatingText(ThemedCanvas):
    """Same props as the component (snake_case).  ``rotation_interval`` is in
    milliseconds.  ``font_size`` is in points.  Colours may be palette tokens
    (``"text"``, ``"tomato"`` …) or hex strings."""

    def __init__(self, parent, texts, *, font_size=26, weight="bold", text="text", bg="bg",
                 highlight_color="tomato", pause_on_hover=False, **engine_kwargs):
        self.dpi = theme.scale(parent)
        self.px = round(font_size * 96 / 72 * self.dpi)
        self._text_color, self._highlight_color, self._bg_token = text, highlight_color, bg
        self.pause_on_hover = pause_on_hover
        engine_kwargs.setdefault("animate", anim.enabled())
        self._kwargs = dict(engine_kwargs, texts=list(texts), weight=weight)
        self.engine = self._build()
        w, h = self.engine.size()
        super().__init__(parent, bg_token=bg, width=w, height=h)
        self._photo = None
        self._image_item = None
        self._wh = (w, h)
        self.loop = anim.FrameLoop(self, self._step)
        if pause_on_hover:
            self.bind("<Enter>", lambda e: setattr(self.engine, "paused", True))
            self.bind("<Leave>", lambda e: setattr(self.engine, "paused", False))
        self._blit()
        self.loop.start()

    def _build(self) -> RotatingTextEngine:
        resolve = lambda v: theme.c(v) if v in ("text", "muted", "tomato", "leaf", "sky", "sun", "plum", "on_tomato") else v  # noqa: E731
        kw = dict(self._kwargs)
        return RotatingTextEngine(
            kw.pop("texts"), font_px=self.px, text_color=resolve(self._text_color),
            bg=theme.c(self._bg_token),
            highlight_color=resolve(self._highlight_color), **kw)

    # ---------------------------------------------------------------- component API

    def next(self) -> None:
        self.engine.next(); self.loop.interval = anim.FRAME_MS; self.loop.start()

    def previous(self) -> None:
        self.engine.previous(); self.loop.interval = anim.FRAME_MS; self.loop.start()

    def jump_to(self, index: int) -> None:
        self.engine.jump_to(index); self.loop.interval = anim.FRAME_MS; self.loop.start()

    def reset(self) -> None:
        self.jump_to(0)

    def set_texts(self, texts) -> None:
        self.engine.set_texts(texts)
        self._blit()

    def set_animate(self, value: bool) -> None:
        self.engine.animate = bool(value)

    # ------------------------------------------------------------------- drawing

    def _step(self, dt: float) -> bool:
        if not self.winfo_ismapped():
            self.loop.interval = 200
            return True
        busy = self.engine.update(dt)
        if busy:
            self._blit()
            self.loop.interval = anim.FRAME_MS
        else:
            self.loop.interval = 100 if self.engine.auto else 250
        return True

    def _blit(self) -> None:
        w, h = self.engine.size()
        if self._wh != (w, h):
            self._wh = (w, h)
            self.configure(width=w, height=h)
        image = self.engine.render()
        if self._photo is None or (self._photo.width(), self._photo.height()) != image.size:
            self._photo = ImageTk.PhotoImage(image)
            if self._image_item is None:
                self._image_item = self.create_image(0, 0, anchor="nw", image=self._photo)
            else:
                self.itemconfigure(self._image_item, image=self._photo)
        else:
            self._photo.paste(image)

    def redraw(self) -> None:
        """Theme changed: rebuild colours, keep the current text."""
        index = self.engine.index
        self.engine = self._build()
        self.engine.index = index
        self.engine.set_texts(self.engine.texts)
        self._blit()
