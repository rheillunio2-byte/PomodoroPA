"""A UI-independent Pomodoro state machine.

The v1 timer decremented a counter from ``after(1000)`` callbacks.  Pausing
left that loop polling and *resume started a second loop*, so after a
pause/resume the clock ran at double speed (and kept doubling).  Here the
clock is derived from a monotonic deadline instead, so there is exactly one
source of truth and nothing to get out of sync:

    timer = PomodoroTimer(work=25, short=5, long=15, interval=4)
    timer.start()
    ...
    event = timer.tick()      # call a few times per second
    if event: ...             # a phase just finished
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Optional

from services.settings_service import load_settings

WORK, SHORT_BREAK, LONG_BREAK = "Work", "Short Break", "Long Break"
MODES = (WORK, SHORT_BREAK, LONG_BREAK)

IDLE, RUNNING, PAUSED = "idle", "running", "paused"


@dataclass(frozen=True)
class PhaseFinished:
    """Returned by :meth:`PomodoroTimer.tick` when a phase completes."""
    finished: str        # the mode that just ended
    next_mode: str       # the mode that is now loaded
    minutes: int         # length of the finished phase
    cycle_count: int     # completed work sessions so far
    auto_started: bool   # whether the next phase is already running


class PomodoroTimer:

    def __init__(self, work: int = 25, short: int = 5, long_break: int = 15,
                 interval: int = 4, auto_start: bool = True,
                 clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self.auto_start = auto_start
        self.mode = WORK
        self.state = IDLE
        self.completed_work = 0
        self._deadline = 0.0
        self.apply_settings(work, short, long_break, interval)
        self._remaining = self.duration(self.mode)

    @classmethod
    def from_settings(cls, **overrides) -> "PomodoroTimer":
        work, short, long_break, interval = load_settings()
        return cls(work, short, long_break, interval, **overrides)

    # ----------------------------------------------------------- configuration

    def apply_settings(self, work: int, short: int, long_break: int, interval: int) -> None:
        self.work_minutes = max(1, int(work))
        self.break_minutes = max(1, int(short))
        self.long_break_minutes = max(1, int(long_break))
        self.long_break_every = max(1, int(interval))
        if getattr(self, "state", IDLE) == IDLE and hasattr(self, "_remaining"):
            self._remaining = self.duration(self.mode)

    def duration(self, mode: Optional[str] = None) -> int:
        """Length of a phase in seconds."""
        mode = mode or self.mode
        minutes = {WORK: self.work_minutes, SHORT_BREAK: self.break_minutes,
                   LONG_BREAK: self.long_break_minutes}[mode]
        return minutes * 60

    # ----------------------------------------------------------------- queries

    @property
    def running(self) -> bool:
        return self.state == RUNNING

    @property
    def paused(self) -> bool:
        return self.state == PAUSED

    @property
    def remaining(self) -> float:
        """Seconds left (fractional)."""
        if self.state == RUNNING:
            return max(0.0, self._deadline - self._clock())
        return self._remaining

    @property
    def seconds_left(self) -> int:
        """Whole seconds left, rounded up so the display reads 00:01 → done."""
        return int(math.ceil(self.remaining - 1e-9))

    @property
    def progress(self) -> float:
        """0.0 at the start of a phase, 1.0 when it is finished."""
        total = self.duration()
        return min(1.0, max(0.0, 1.0 - self.remaining / total))

    @property
    def cycle_position(self) -> int:
        """Work sessions finished in the current long-break cycle (0 … interval-1)."""
        return self.completed_work % self.long_break_every

    # ---------------------------------------------------------------- commands

    def start(self) -> None:
        if self.state == RUNNING:
            return
        if self._remaining <= 0:
            self._remaining = self.duration()
        self._deadline = self._clock() + self._remaining
        self.state = RUNNING

    def pause(self) -> None:
        if self.state != RUNNING:
            return
        self._remaining = self.remaining
        self.state = PAUSED

    def resume(self) -> None:
        if self.state == PAUSED:
            self.start()

    def toggle(self) -> str:
        """Start / pause / resume.  Returns the new state."""
        if self.state == RUNNING:
            self.pause()
        else:
            self.start()
        return self.state

    def reset(self) -> None:
        """Back to the start of the *current* phase."""
        self.state = IDLE
        self._remaining = self.duration()

    def reset_all(self) -> None:
        """Back to a fresh work phase and a fresh cycle."""
        self.mode = WORK
        self.completed_work = 0
        self.reset()

    def set_mode(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(f"Unknown mode: {mode}")
        self.mode = mode
        self.reset()

    def skip(self) -> PhaseFinished:
        """Jump to the next phase without crediting the current one."""
        return self._advance(credit=False)

    # -------------------------------------------------------------------- tick

    def tick(self) -> Optional[PhaseFinished]:
        """Advance the clock; returns a :class:`PhaseFinished` exactly once per phase."""
        if self.state == RUNNING and self._clock() >= self._deadline:
            return self._advance(credit=True)
        return None

    def _advance(self, credit: bool) -> PhaseFinished:
        finished, minutes = self.mode, self.duration() // 60
        if finished == WORK and credit:
            self.completed_work += 1
        if finished == WORK:
            take_long = credit and self.completed_work % self.long_break_every == 0
            self.mode = LONG_BREAK if take_long else SHORT_BREAK
        else:
            self.mode = WORK
        self._remaining = self.duration()
        self.state = IDLE
        auto = bool(self.auto_start)
        if auto:
            self.start()
        return PhaseFinished(finished, self.mode, minutes, self.completed_work, auto)
