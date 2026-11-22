"""Shared test helpers (standard library only – no pytest needed)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DatabaseTestCase(unittest.TestCase):
    """Each test runs against its own empty, freshly migrated database."""

    def setUp(self):
        import config
        from services import db

        self._tmp = tempfile.TemporaryDirectory()
        self._original = config.DB_PATH
        config.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_db()

    def tearDown(self):
        import config

        config.DB_PATH = self._original
        self._tmp.cleanup()
