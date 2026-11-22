"""Short feedback sounds, played off the UI thread.

v1 imported ``winsound`` at module level (crashing on macOS/Linux) and called
``winsound.Beep`` directly, which blocks for its full duration and froze the
window for half a second.
"""
from __future__ import annotations

import subprocess
import sys
import threading

from services.settings_service import get_settings


def _beeps(sequence) -> None:
    try:
        if sys.platform == "win32":
            import winsound
            for frequency, duration in sequence:
                winsound.Beep(frequency, duration)
        elif sys.platform == "darwin":
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                           check=False, timeout=5, capture_output=True)
        # Other platforms: stay silent rather than write a BEL to stdout.
    except Exception:
        pass


def _play(sequence, force: bool = False) -> None:
    try:
        if not force and not get_settings()["sounds"]:
            return
    except Exception:
        return
    threading.Thread(target=_beeps, args=(sequence,), daemon=True).start()


def play_success(force: bool = False) -> None:
    _play([(880, 120), (1175, 180)], force)


def play_break(force: bool = False) -> None:
    _play([(660, 140), (523, 220)], force)


def play_error(force: bool = False) -> None:
    _play([(300, 220)], force)
