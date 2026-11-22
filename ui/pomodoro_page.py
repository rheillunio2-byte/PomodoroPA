"""The timer."""
from __future__ import annotations

import math
import time

import customtkinter as ctk

import config
from services import session_service, task_service
from services.notification_service import notify
from services.pomodoro_service import LONG_BREAK, SHORT_BREAK, WORK, PomodoroTimer, PhaseFinished
from services.sound_service import play_break, play_success
from ui import theme
from ui.pages_base import BasePage
from ui.widgets.components import Button, label
from ui.widgets.ring import Ring
from ui.widgets.rotating_text import RotatingText

MODES = (WORK, SHORT_BREAK, LONG_BREAK)
LABELS = {WORK: "Focus", SHORT_BREAK: "Short break", LONG_BREAK: "Long break"}
FROM_LABEL = {v: k for k, v in LABELS.items()}
NO_TASK = "No task selected"


class PomodoroPage(BasePage):
    title = "Pomodoro"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        s = app.settings
        self.timer = PomodoroTimer.from_settings(auto_start=bool(s["auto_start"]))
        self.task_id: int | None = None
        self.task_choices: dict[str, int] = {}
        self._start_state = None

        col = ctk.CTkFrame(self, fg_color="transparent")
        col.pack(expand=True)

        self.mode_picker = ctk.CTkSegmentedButton(
            col, values=[LABELS[m] for m in MODES], command=self._pick_mode, height=34,
            font=theme.font(12, "bold"), corner_radius=10,
            fg_color=theme.pair("surface2"), unselected_color=theme.pair("surface2"),
            unselected_hover_color=theme.pair("surface3"), selected_color=theme.pair("tomato"),
            selected_hover_color=theme.pair("tomato_hi"), text_color=theme.pair("text"))
        self.mode_picker.set(LABELS[WORK])
        self.mode_picker.pack(pady=(4, 12))

        self.ring = Ring(col, size=280, thickness=15, bg="bg")
        self.ring.pack()

        self.phase_text = RotatingText(
            col, [LABELS[m] for m in MODES], font_size=21, weight="bold", effect="flip", direction="up",
            stagger_duration=0.02, auto=False, bg="bg", rotation_interval=999999, overflow_hidden=False,
            animate=bool(s["animations"]))
        self.phase_text.pack(pady=(10, 2))

        self.status = label(col, "", 12, tone="muted")
        self.status.pack()

        self.task_menu = ctk.CTkOptionMenu(
            col, values=[NO_TASK], width=300, height=36, corner_radius=10, command=self._pick_task,
            fg_color=theme.pair("surface2"), button_color=theme.pair("surface3"),
            button_hover_color=theme.pair("border"), text_color=theme.pair("text"),
            dropdown_fg_color=theme.pair("surface2"), dropdown_text_color=theme.pair("text"),
            dropdown_hover_color=theme.pair("surface3"), font=theme.font(12))
        self.task_menu.pack(pady=(14, 14))

        buttons = ctk.CTkFrame(col, fg_color="transparent")
        buttons.pack()
        self.start_button = Button(buttons, "Start", self.toggle, kind="primary", icon_name="play",
                                   width=150, height=46)
        self.start_button.pack(side="left", padx=5)
        Button(buttons, "Reset", self.reset_timer, kind="ghost", icon_name="reset", width=100, height=46).pack(side="left", padx=5)
        Button(buttons, "Skip", self.skip_phase, kind="ghost", icon_name="skip", width=100, height=46).pack(side="left", padx=5)

        self.cycle = label(col, "", 16, "bold", tone="tomato")
        self.cycle.pack(pady=(16, 0))
        self.today = label(col, "", 11, tone="muted")
        self.today.pack(pady=(2, 0))
        hint = label(col, "Space start/pause   R reset   S skip", 10, tone="faint")
        hint.pack(pady=(10, 0))

        self._refresh_today()
        self._after_mode_change(animate=False)
        self._tick()

    # --------------------------------------------------------------- public API

    def toggle(self) -> None:
        self.timer.toggle()
        self._render()
        self.app.refresh_badges()

    def reset_timer(self) -> None:
        self.timer.reset()
        self._render()
        self.app.refresh_badges()

    def skip_phase(self) -> None:
        self.timer.skip()
        self._after_mode_change()
        self.app.refresh_badges()

    def set_current_task(self, task_id, title=None) -> None:
        self.task_id = task_id
        self.refresh_tasks()

    def apply_settings(self) -> None:
        s = self.app.settings
        self.timer.apply_settings(s["work_minutes"], s["short_break"], s["long_break"], s["long_break_every"])
        self.timer.auto_start = bool(s["auto_start"])
        self.phase_text.set_animate(bool(s["animations"]))
        self._after_mode_change(animate=False)

    # ------------------------------------------------------------------ lifecycle

    def on_show(self) -> None:
        self.refresh_tasks()
        self._refresh_today()
        self._render()

    def _refresh_today(self) -> None:
        count = session_service.work_sessions_today()
        self.today.configure(text=f"{count} focus session{'s' if count != 1 else ''} today")

    def refresh_tasks(self) -> None:
        rows = task_service.get_tasks(status="Active")
        self.task_choices = {}
        for task_id, title, *_ in rows:
            name = title if title not in self.task_choices else f"{title} (#{task_id})"
            self.task_choices[name] = task_id
        values = [NO_TASK] + list(self.task_choices)
        self.task_menu.configure(values=values)
        current = next((n for n, i in self.task_choices.items() if i == self.task_id), None)
        if current is None:
            self.task_id = None
        self.task_menu.set(current or NO_TASK)

    def _pick_task(self, name: str) -> None:
        self.task_id = self.task_choices.get(name)

    def _pick_mode(self, display: str) -> None:
        self.timer.set_mode(FROM_LABEL[display])
        self._after_mode_change()
        self.app.refresh_badges()

    # ----------------------------------------------------------------------- loop

    def _tick(self) -> None:
        event = self.timer.tick()
        if event:
            self._phase_finished(event)
        self._render()
        self.after(100 if self.timer.running else 400, self._tick)

    def _phase_finished(self, event: PhaseFinished) -> None:
        kind = {WORK: session_service.WORK, SHORT_BREAK: session_service.SHORT_BREAK,
                LONG_BREAK: session_service.LONG_BREAK}[event.finished]
        session_service.save_session(event.minutes, kind, self.task_id if event.finished == WORK else None)
        if event.finished == WORK:
            if self.task_id is not None:
                task_service.add_pomodoro(self.task_id)
            play_success()
            self.ring.burst()
            message = "Focus session complete. Time for a break."
            notify("Pomodoro complete", message)
        else:
            play_break()
            message = "Break over. Ready to focus?"
            notify("Break finished", message)
        self.app.toast(message, "success")
        self._refresh_today()
        self._after_mode_change()
        self.app.refresh_badges()

    # -------------------------------------------------------------------- display

    def _after_mode_change(self, animate: bool = True) -> None:
        mode = self.timer.mode
        self.ring.set_colors(mode)
        self.mode_picker.set(LABELS[mode])
        self.phase_text.jump_to(MODES.index(mode)) if animate else None
        token = {WORK: "tomato", SHORT_BREAK: "leaf", LONG_BREAK: "sky"}[mode]
        self.cycle.configure(text_color=theme.pair(token))
        self._render()

    def _render(self) -> None:
        t = self.timer
        secs = t.seconds_left
        glow = 0.55 + 0.45 * math.sin(time.time() * math.tau / 3.0) if t.running else 0.0
        self.ring.set_progress(t.progress, glow)
        self.ring.set_text(f"{secs // 60:02d}:{secs % 60:02d}",
                           f"Session {t.cycle_position + 1} of {t.long_break_every}" if t.mode == WORK else "Recharge")

        state = (t.state, t.mode)
        if state != self._start_state:
            self._start_state = state
            if t.running:
                self.start_button.configure(text="Pause")
                self.start_button.configure(image=self._icon("pause"))
            else:
                self.start_button.configure(text="Resume" if t.paused else "Start")
                self.start_button.configure(image=self._icon("play"))
            self.status.configure(text={"running": "In progress", "paused": "Paused",
                                        "idle": "Ready when you are"}[t.state])

        interval = t.long_break_every
        if interval <= 8:
            done = t.cycle_position
            self.cycle.configure(text="  ".join("●" if i < done else "○" for i in range(interval)))
        else:
            self.cycle.configure(text=f"{t.cycle_position} / {interval} to long break")
        if t.running:
            self.app.title(f"{secs // 60:02d}:{secs % 60:02d}  {LABELS[t.mode]} · {config.APP_NAME}")
        elif self.app.title() != config.APP_NAME:
            self.app.title(config.APP_NAME)

    @staticmethod
    def _icon(name: str):
        from ui.widgets.components import icon
        return icon(name, 16, "on_tomato")
