"""Central configuration for FocusFlow.

Everything that used to be a hard-coded, working-directory-relative path
("database/focusflow.db") lives here, so the app behaves the same no matter
where it is launched from.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "FocusFlow"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Rheil Evans T. Lunio"
APP_TAGLINE = "Focus deeper. Finish more."
REPO_URL = "https://github.com/rheillunio2-byte/PomodoroPA"
LICENSE_NAME = "MIT"

BASE_DIR = Path(__file__).resolve().parent


def _data_dir() -> Path:
    """Where the SQLite database lives.

    * Running from source  -> ``<project>/database``
    * Frozen (PyInstaller) -> a per-user folder, because the install
      directory is usually read-only.
    """
    if getattr(sys, "frozen", False):
        root = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME") or Path.home()
        return Path(root) / APP_NAME
    return BASE_DIR / "database"


DATA_DIR = _data_dir()

# FOCUSFLOW_DB lets tests (and power users) point the app at another file.
DB_PATH = Path(os.environ.get("FOCUSFLOW_DB", DATA_DIR / "focusflow.db"))

# Task vocabularies shared by the UI and the services.
CATEGORIES = ["Study", "Work", "Personal", "Health"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
