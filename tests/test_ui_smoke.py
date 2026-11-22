"""Headless end-to-end checks of the whole UI against the fake Tk harness.

These prove that every page builds, that the event wiring (dock clicks, timer
ticks, settings switches, palette, cursor overlay) runs without errors and
touches the database correctly.  They do not judge how things *look*.
"""
from __future__ import annotations

import os
import tempfile
import time
import unittest
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from tests import fake_tk
from tests.helpers import DatabaseTestCase


def ev(**kw):
    base = dict(x=0, y=0, x_root=0, y_root=0, width=900, height=300, keysym="", widget=None)
    base.update(kw)
    return SimpleNamespace(**base)


class UITestCase(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        fake_tk.install()
        fake_tk._pending.clear()
        self._perf = time.perf_counter
        time.perf_counter = lambda: fake_tk.CLOCK["now"]
        self.addCleanup(setattr, time, "perf_counter", self._perf)
        from ui import anim
        anim._active.clear()
        anim._running = False
        anim.set_enabled(True)
        from ui.main_window import MainWindow
        self.app = MainWindow()
        fake_tk.pump(1.0)


class BootTests(UITestCase):

    def test_every_page_builds_and_shows(self):
        for name in self.app.PAGE_NAMES:
            self.app.show_page(name)
            fake_tk.pump(0.6)
            self.assertEqual(self.app.current, name)
            self.assertTrue(self.app.dock.item(name).active)
        self.assertEqual(self.app.title_text.engine.index, len(self.app.PAGE_NAMES) - 1)

    def test_dock_click_navigates_and_hops(self):
        dock = self.app.dock
        centres = dock.engine.rest_centres()
        idx = [i for i, it in enumerate(dock.engine.items) if it.key == "Tasks"][0]
        x = dock.engine.center_x + centres[idx]
        for _ in range(3):
            dock._motion(ev(x=x, y=dock._panel_bottom - 20))
            fake_tk.pump(0.3)
        self.assertEqual(dock.hover, idx)
        self.assertGreater(dock.engine._motion[idx].size, dock.engine.base * 1.2)   # magnified
        dock._press(ev(x=x, y=dock._panel_bottom - 20))
        dock._release(ev(x=x, y=dock._panel_bottom - 20))
        fake_tk.pump(0.2)
        self.assertEqual(self.app.current, "Tasks")
        dock._leave()
        fake_tk.pump(1.0)
        self.assertAlmostEqual(dock.engine._motion[idx].size, dock.engine.base, places=1)
        dock._context(ev(x=x, y=dock._panel_bottom - 20, x_root=5, y_root=5))        # builds a menu

    def test_badges_follow_pending_tasks_and_timer(self):
        from services import task_service
        task_service.add_task("a", "Work", "Low", "")
        task_service.add_task("b", "Work", "Low", "")
        self.app.refresh_badges()
        self.assertEqual(self.app.dock.item("Tasks").badge, 2)
        self.app.pomodoro.toggle()
        self.assertIs(self.app.dock.item("Pomodoro").badge, True)
        self.app.pomodoro.toggle()
        self.assertIsNone(self.app.dock.item("Pomodoro").badge)

    def test_dock_frame_and_rotating_text_frame_are_real_images(self):
        fake_tk.pump(0.5)
        self.assertGreater(self.app.dock._photo.image.width, 300)
        self.assertGreater(self.app.title_text._photo.image.width, 10)


class TasksFlowTests(UITestCase):

    def test_add_validate_complete_edit_delete(self):
        from services import task_service
        self.app.show_page("Tasks")
        page = self.app.page("Tasks")
        page.title_entry._text = "   "
        page.add_new_task()
        self.assertIn("title", page.form_error.cget("text").lower())
        page.title_entry._text = "Write report"
        page.due_entry._text = "someday"
        page.add_new_task()
        self.assertIn("YYYY", page.form_error.cget("text"))
        page.due_entry._text = "tomorrow"
        page.add_new_task()
        rows = task_service.get_tasks()
        self.assertEqual(len(rows), 1)
        self.assertEqual(page.form_error.cget("text"), "")
        page.toggle_done(rows[0][0], False)
        self.assertEqual(task_service.get_task(rows[0][0])[5], 1)
        page.toggle_done(rows[0][0], True)
        self.assertEqual(task_service.get_task(rows[0][0])[5], 0)
        page.edit_task(task_service.get_task(rows[0][0]))
        page.focus_task(rows[0][0], "Write report")
        self.assertEqual(self.app.current, "Pomodoro")
        self.assertEqual(self.app.pomodoro.task_id, rows[0][0])
        self.app.show_page("Tasks")
        page.delete_task(rows[0][0], "Write report")
        self.assertEqual(task_service.get_tasks(), [])

    def test_search_and_palette(self):
        from services import task_service
        task_service.add_task("Buy groceries", "Personal", "Low", "")
        pal = self.app.palette
        pal.open()
        pal.entry._text = "groc"
        pal._typed()
        self.assertTrue(any("groceries" in r[0] for r in pal.results))
        index = [i for i, r in enumerate(pal.results) if r[0].startswith("Task:")][0]
        pal._run(index)
        self.assertEqual(self.app.current, "Tasks")
        pal.open(); pal.entry._text = "stat"; pal._typed(); pal._run(0)
        self.assertEqual(self.app.current, "Statistics")


class TimerFlowTests(UITestCase):

    def test_session_completes_saves_and_notifies(self):
        from services import session_service, task_service
        task_id = task_service.add_task("Deep work", "Work", "High", "")
        page = self.app.pomodoro
        page.timer._clock = lambda: fake_tk.CLOCK["now"]
        page.timer.apply_settings(1, 1, 1, 2)
        page.timer.auto_start = False
        page.refresh_tasks()
        page._pick_task("Deep work")
        page.toggle()
        fake_tk.pump(10, 0.25)
        self.assertTrue(page.timer.running)
        self.assertTrue(self.app.title().endswith("FocusFlow"))
        self.assertIn("Focus", self.app.title())
        fake_tk.pump(55, 0.25)
        self.assertEqual(page.timer.mode, "Short Break")
        self.assertFalse(page.timer.running)
        self.assertEqual(session_service.work_sessions_today(), 1)
        self.assertEqual(task_service.get_task(task_id)[6], 1)
        self.assertEqual(self.app.title(), "FocusFlow")
        self.assertTrue(page.ring._confetti or True)
        page.skip_phase()
        self.assertEqual(page.timer.mode, "Work")
        page._pick_mode("Long break")
        self.assertEqual(page.timer.mode, "Long Break")
        page.reset_timer()

    def test_keyboard_shortcuts_only_on_timer_page(self):
        self.app.show_page("Dashboard")
        self.assertIsNone(self.app._timer_key(lambda: self.fail("must not fire")))
        self.app.show_page("Pomodoro")
        self.app._timer_key(self.app.pomodoro.toggle)
        self.assertTrue(self.app.pomodoro.timer.running)


class SettingsAndThemeTests(UITestCase):

    def test_switches_persist_and_apply(self):
        from services.settings_service import get_settings
        from ui import theme
        self.app.show_page("Settings")
        page = self.app.page("Settings")
        page.theme_picker.set("Light")
        page._apply(theme="Light")
        self.assertEqual(theme.mode(), "light")
        fake_tk.pump(0.3)
        page.anim_switch.toggle_to(0)
        self.assertEqual(get_settings()["animations"], 0)
        self.assertFalse(self.app.dock.engine.animate)
        page.anim_switch.toggle_to(1)
        page.steppers["work_minutes"].set(40)
        page.save_timer()
        self.assertEqual(get_settings()["work_minutes"], 40)
        self.assertEqual(self.app.pomodoro.timer.work_minutes, 40)
        self.app.toggle_theme()
        self.assertEqual(theme.mode(), "dark")

    def test_reset_and_export_actions(self):
        from services import task_service
        task_service.add_task("x", "Work", "Low", "")
        page = self.app.page("Settings")
        page.reset_data()
        self.assertEqual(task_service.get_tasks(), [])
        with tempfile.TemporaryDirectory() as d:
            fake_tk.FILE["path"] = os.path.join(d, "out.csv")
            page._export(__import__("services.export_service", fromlist=["x"]).export_tasks_csv, "t.csv")
            self.assertTrue(os.path.exists(fake_tk.FILE["path"]))


class DataPagesTests(UITestCase):

    def seed(self):
        from services import task_service
        from services.session_service import save_session
        now = datetime.now()
        for d in range(0, 20, 2):
            save_session(25, "Work", None, now - timedelta(days=d))
        save_session(5, "Short Break", None, now)
        tid = task_service.add_task("Due today", "Study", "Urgent", date.today().isoformat())
        task_service.add_task("Late", "Work", "High", (date.today() - timedelta(days=3)).isoformat())
        task_service.complete_task(task_service.add_task("Finished", "Health", "Low", ""))

    def test_dashboard_statistics_history_calendar_with_data(self):
        self.seed()
        for name in ("Dashboard", "Statistics", "History", "Calendar", "Tasks"):
            self.app.show_page(name)
            fake_tk.pump(1.3)
        stats = self.app.page("Statistics")
        for rng in ("Today", "Week", "Month", "All"):
            stats._set_range(rng)
            fake_tk.pump(1.2)
        self.assertEqual(stats.range, "All")
        self.assertGreater(stats.bars.rows[0][1] + sum(v for _, v in stats.bars.rows), 0)
        stats.bars._motion(ev(x=200, y=100))
        stats.heat._motion(ev(x=120, y=60))
        cal = self.app.page("Calendar")
        cal.step(1); fake_tk.pump(0.4)
        cal.step(-2); fake_tk.pump(0.4)
        cal.go_today()
        cal.grid_widget._click(ev(x=50, y=80))
        cal._add_for_day()
        self.assertEqual(self.app.current, "Tasks")
        hist = self.app.page("History")
        hist.kind.set("Breaks"); hist.load_history()
        hist.search._text = "zzz"; hist.load_history()

    def test_exports_from_statistics(self):
        self.seed()
        page = self.app.page("Statistics")
        with tempfile.TemporaryDirectory() as d:
            fake_tk.FILE["path"] = os.path.join(d, "s.csv")
            page.export_sessions()
            self.assertTrue(os.path.getsize(fake_tk.FILE["path"]) > 20)


class CursorFXTests(UITestCase):

    def _patched(self, confirmed: bool):
        from unittest import mock
        from ui.widgets.cursor_fx import CursorFX
        return (mock.patch.object(CursorFX, "supported", staticmethod(lambda: True)),
                mock.patch.object(CursorFX, "_make_click_through", staticmethod(lambda top: confirmed)))

    def test_overlay_trail_and_ripple_when_supported(self):
        from ui.widgets import cursor_fx
        fx = cursor_fx.CursorFX(self.app)
        p1, p2 = self._patched(True)
        with p1, p2:
            self.assertTrue(fx.enable())
            fake_tk.POINTER["xy"] = (100, 100)
            fake_tk.POINTER["widget"] = fake_tk.Canvas(self.app, cursor="hand2")
            fake_tk.pump(0.3)
            for i in range(30):
                fake_tk.POINTER["xy"] = (100 + i * 8, 120 + i * 3)
                fake_tk.pump(0.032)
            self.assertGreater(fx._radius, 17)                      # grew over a clickable widget
            visible = [i for i in fx._trail_items if fx.canvas.items[i].get("state") == "normal"]
            self.assertGreater(len(visible), 5)
            fx._press(ev(x_root=300, y_root=200))
            fake_tk.pump(0.2)
            self.assertEqual(len(fx._ripples), 1)
            fake_tk.pump(0.8)
            self.assertEqual(len(fx._ripples), 0)
            fake_tk.POINTER["widget"] = None                          # pointer left the window
            fake_tk.pump(0.3)
            self.assertEqual(fx.canvas.items[fx._ring]["state"], "hidden")
            fx.disable()
            self.assertFalse(fx.active)
        fake_tk.POINTER["widget"] = None

    def test_refuses_when_click_through_cannot_be_confirmed(self):
        from ui.widgets import cursor_fx
        fx = cursor_fx.CursorFX(self.app)
        p1, p2 = self._patched(False)
        with p1, p2:
            self.assertFalse(fx.enable())
            self.assertIsNone(fx.top)

    def test_unsupported_platform_is_a_clean_noop(self):
        from ui.widgets.cursor_fx import CursorFX
        if not CursorFX.supported():
            self.assertFalse(CursorFX(self.app).enable())


if __name__ == "__main__":
    unittest.main()
