from __future__ import annotations

import sqlite3
import unittest
from datetime import date, datetime, timedelta

from tests.helpers import DatabaseTestCase


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class DatabaseTests(DatabaseTestCase):

    def test_init_is_idempotent(self):
        from services import db
        db.init_db()
        db.init_db()
        with db.connect() as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"tasks", "sessions", "settings"} <= tables)

    def test_migrates_a_v1_database_in_place(self):
        import config
        from services import db
        config.DB_PATH.unlink()
        conn = sqlite3.connect(config.DB_PATH)  # the exact v1.0 layout
        conn.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,"
                     " category TEXT, priority TEXT, due_date TEXT, completed INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, completed_at TEXT, minutes INTEGER)")
        conn.execute("CREATE TABLE settings(id INTEGER PRIMARY KEY, work_minutes INTEGER, short_break INTEGER,"
                     " long_break INTEGER, long_break_every INTEGER)")
        conn.execute("INSERT INTO settings VALUES (1, 30, 6, 20, 3)")
        conn.execute("INSERT INTO sessions (completed_at, minutes) VALUES ('2026-07-24 10:37:07', 25)")
        conn.commit()
        conn.close()

        db.init_db()

        from services.settings_service import get_settings
        s = get_settings()
        self.assertEqual((s["work_minutes"], s["short_break"], s["long_break"], s["long_break_every"]), (30, 6, 20, 3))
        self.assertEqual(s["theme"], "Dark")
        with db.connect() as c:
            self.assertEqual(c.execute("SELECT session_type FROM sessions").fetchone()[0], "Work")
            cols = {r[1] for r in c.execute("PRAGMA table_info(tasks)")}
        self.assertIn("pomodoros", cols)
        self.assertIn("completed_at", cols)


class SettingsTests(DatabaseTestCase):

    def test_defaults_and_roundtrip(self):
        from services.settings_service import get_settings, update_settings, load_settings
        self.assertEqual(get_settings()["work_minutes"], 25)
        update_settings(work_minutes=50, theme="Light", cursor_fx=0)
        s = get_settings()
        self.assertEqual((s["work_minutes"], s["theme"], s["cursor_fx"]), (50, "Light", 0))
        self.assertEqual(load_settings()[0], 50)

    def test_validation(self):
        from services.settings_service import update_settings
        with self.assertRaises(ValueError):
            update_settings(work_minutes=0)
        with self.assertRaises(ValueError):
            update_settings(work_minutes="abc")
        with self.assertRaises(ValueError):
            update_settings(theme="Neon")
        with self.assertRaises(KeyError):
            update_settings(nonsense=1)


class TaskTests(DatabaseTestCase):

    def test_due_date_parsing(self):
        from services.task_service import parse_due_date
        today = date(2026, 7, 24)
        self.assertEqual(parse_due_date("", today), "")
        self.assertEqual(parse_due_date("today", today), "2026-07-24")
        self.assertEqual(parse_due_date("Tomorrow", today), "2026-07-25")
        self.assertEqual(parse_due_date("2026/8/3", today), "2026-08-03")
        for bad in ("next friday", "2026-13-01", "31/12/2026"):
            with self.assertRaises(ValueError):
                parse_due_date(bad, today)

    def test_add_validate_and_order_by_priority(self):
        from services import task_service as t
        t.add_task("low one", "Study", "Low", "")
        t.add_task("urgent one", "Work", "Urgent", "2026-09-01")
        t.add_task("medium one", "Study", "Medium", "")
        titles = [r[1] for r in t.get_tasks()]
        self.assertEqual(titles, ["urgent one", "medium one", "low one"])  # v1 sorted these alphabetically
        with self.assertRaises(ValueError):
            t.add_task("   ", "Study", "Low", "")
        with self.assertRaises(ValueError):
            t.add_task("x", "Nope", "Low", "")
        with self.assertRaises(ValueError):
            t.add_task("x", "Study", "Low", "someday")

    def test_filters_complete_reopen_delete(self):
        from services import task_service as t
        a = t.add_task("Read 100% of chapter_1", "Study", "High", "")
        b = t.add_task("Gym", "Health", "Low", "")
        self.assertEqual([r[1] for r in t.get_tasks(search="100%")], ["Read 100% of chapter_1"])  # wildcard escaped
        self.assertEqual(len(t.get_tasks(search="%")), 1)
        self.assertEqual([r[1] for r in t.get_tasks(category="Health")], ["Gym"])
        t.complete_task(a)
        self.assertEqual([r[1] for r in t.get_tasks(status="Done")], ["Read 100% of chapter_1"])
        self.assertEqual([r[1] for r in t.get_tasks()][0], "Gym")      # open tasks first
        t.reopen_task(a)
        self.assertEqual(len(t.get_tasks(status="Active")), 2)
        t.delete_task(b)
        self.assertIsNone(t.get_task(b))

    def test_add_pomodoro_and_pending_count(self):
        from services import task_service as t
        i = t.add_task("Focus", "Work", "Medium", "")
        t.add_pomodoro(i)
        t.add_pomodoro(i)
        self.assertEqual(t.get_task(i)[6], 2)
        self.assertEqual(t.count_pending(), 1)


class TimerTests(unittest.TestCase):

    def make(self, **kw):
        clock = FakeClock()
        from services.pomodoro_service import PomodoroTimer
        return PomodoroTimer(work=25, short=5, long_break=15, interval=2, clock=clock, **kw), clock

    def test_pause_resume_does_not_change_the_speed_of_time(self):
        """Regression: v1 started a second countdown loop on every resume."""
        timer, clock = self.make()
        timer.start()
        clock.advance(60)
        timer.pause()
        clock.advance(500)                       # paused time must not count
        self.assertAlmostEqual(timer.remaining, 25 * 60 - 60)
        timer.resume()
        clock.advance(30)
        self.assertAlmostEqual(timer.remaining, 25 * 60 - 90)   # not -120 / -150
        self.assertEqual(timer.seconds_left, 25 * 60 - 90)

    def test_cycle_work_short_work_long(self):
        timer, clock = self.make(auto_start=False)
        seen = []
        for _ in range(4):
            timer.start()
            clock.advance(timer.duration() + 1)
            event = timer.tick()
            seen.append((event.finished, event.next_mode))
            self.assertIsNone(timer.tick())      # fires once only
        self.assertEqual(seen, [("Work", "Short Break"), ("Short Break", "Work"),
                                ("Work", "Long Break"), ("Long Break", "Work")])
        self.assertEqual(timer.completed_work, 2)

    def test_auto_start_continues_into_next_phase(self):
        timer, clock = self.make(auto_start=True)
        timer.start()
        clock.advance(25 * 60)
        event = timer.tick()
        self.assertTrue(event.auto_started)
        self.assertTrue(timer.running)
        self.assertEqual(timer.mode, "Short Break")
        self.assertEqual(timer.seconds_left, 5 * 60)

    def test_skip_does_not_credit_or_trigger_long_break(self):
        timer, clock = self.make(auto_start=False)
        event = timer.skip()
        self.assertEqual((event.finished, event.next_mode, timer.completed_work), ("Work", "Short Break", 0))

    def test_reset_progress_and_settings(self):
        timer, clock = self.make()
        timer.start()
        clock.advance(300)
        self.assertAlmostEqual(timer.progress, 300 / 1500)
        timer.reset()
        self.assertFalse(timer.running)
        self.assertEqual(timer.seconds_left, 1500)
        timer.apply_settings(50, 10, 30, 4)
        self.assertEqual(timer.seconds_left, 3000)   # idle timers pick up new durations


class StatsTests(DatabaseTestCase):

    def seed(self):
        from services.session_service import save_session
        now = datetime.now()
        for days_ago, minutes, kind in [(0, 25, "Work"), (0, 25, "Work"), (0, 5, "Short Break"),
                                        (1, 25, "Work"), (3, 50, "Work"), (40, 25, "Work")]:
            save_session(minutes, kind, when=now - timedelta(days=days_ago))

    def test_ranges_count_only_work_sessions(self):
        from services.statistics_service import get_statistics
        self.seed()
        self.assertEqual(get_statistics("Today")["sessions"], 2)
        self.assertEqual(get_statistics("Today")["focus"], 50)
        self.assertEqual(get_statistics("Week")["sessions"], 4)
        self.assertEqual(get_statistics("Month")["sessions"], 4)
        self.assertEqual(get_statistics("All")["sessions"], 5)
        self.assertEqual(get_statistics("All")["today"], 50)

    def test_daily_focus_fills_empty_days(self):
        from services.chart_service import daily_focus, focus_series, task_categories
        self.seed()
        rows = daily_focus(7)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-1][1:], (50, 2))
        self.assertEqual(rows[0][1:], (0, 0))
        title, bars = focus_series("Today")
        self.assertEqual(len(bars), 24)
        self.assertEqual(len(focus_series("All")[1]), 12)
        self.assertEqual(task_categories(), [])

    def test_streaks(self):
        from services.streak_service import streaks
        from services.session_service import save_session
        now = datetime.now()
        self.assertEqual(streaks(), (0, 0))
        for d in (0, 1, 2, 5, 6, 7, 8):
            save_session(25, "Work", when=now - timedelta(days=d))
        self.assertEqual(streaks(), (3, 4))
        # Worked yesterday but not yet today: the streak is still alive.
        from services import db
        with db.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE substr(completed_at,1,10)=?", (date.today().isoformat(),))
        self.assertEqual(streaks()[0], 2)

    def test_dashboard_achievements_and_insights(self):
        from services.dashboard_service import get_dashboard_stats
        from services.achievement_service import get_achievements
        from services.insight_service import get_insights
        from services import task_service as t
        self.seed()
        t.complete_task(t.add_task("Done", "Work", "Low", ""))
        t.add_task("Late", "Work", "High", (date.today() - timedelta(days=2)).isoformat())
        stats = get_dashboard_stats()
        self.assertEqual((stats["pomodoros"], stats["focus_minutes"], stats["today_pomodoros"]), (5, 150, 2))
        self.assertEqual((stats["completed"], stats["pending"], stats["overdue"]), (1, 1, 1))
        badges = {a["key"]: a for a in get_achievements()}
        self.assertTrue(badges["first"]["unlocked"])
        self.assertFalse(badges["ten"]["unlocked"])
        self.assertEqual(badges["ten"]["progress"], 5)
        insights = get_insights()
        self.assertTrue(insights["metrics"] and insights["tips"])

    def test_empty_database_is_fine(self):
        from services.dashboard_service import get_dashboard_stats
        from services.insight_service import get_insights
        from services.statistics_service import get_statistics
        self.assertEqual(get_dashboard_stats()["pomodoros"], 0)
        self.assertEqual(get_statistics("All")["completion"], 0)
        self.assertIn("first Pomodoro", get_insights()["tips"][0])


class CalendarHistoryExportTests(DatabaseTestCase):

    def test_calendar_queries(self):
        from services import calendar_service as c, task_service as t
        today = date.today()
        t.add_task("Today A", "Work", "Low", today.isoformat())
        t.add_task("Today B", "Work", "Urgent", today.isoformat())
        t.add_task("Past", "Work", "Low", (today - timedelta(days=1)).isoformat())
        t.add_task("Future", "Work", "Medium", (today + timedelta(days=3)).isoformat())
        self.assertEqual([r[1] for r in c.get_tasks_by_date(today.isoformat())], ["Today B", "Today A"])
        month = c.get_month_summary(today.year, today.month)
        self.assertEqual(month[today.isoformat()]["total"], 2)
        self.assertEqual(month[today.isoformat()]["rank"], 4)
        self.assertEqual({r[0] for r in c.get_upcoming_tasks()}, {"Today A", "Today B", "Future"})
        self.assertEqual([r[0] for r in c.get_overdue_tasks()], ["Past"])

    def test_history_filters_and_task_join(self):
        from services import task_service as t
        from services.history_service import get_history
        from services.session_service import save_session
        task = t.add_task("Write essay", "Study", "High", "")
        now = datetime.now()
        save_session(25, "Work", task, now)
        save_session(5, "Short Break", None, now)
        save_session(25, "Work", None, now - timedelta(days=20))
        self.assertEqual(len(get_history("All Time")), 3)
        self.assertEqual(len(get_history("Today")), 2)
        self.assertEqual(len(get_history("This Month")), 3)
        self.assertEqual(len(get_history("All Time", session_type="Breaks")), 1)
        rows = get_history("All Time", search="essay")
        self.assertEqual((len(rows), rows[0][3]), (1, "Write essay"))

    def test_csv_export(self):
        import csv, os, tempfile
        from services import task_service as t
        from services.export_service import export_sessions_csv, export_tasks_csv
        from services.session_service import save_session
        t.add_task('Quote "me", please', "Work", "Low", "")
        save_session(25, "Work")
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(export_sessions_csv(os.path.join(d, "s.csv")), 1)
            self.assertEqual(export_tasks_csv(os.path.join(d, "t.csv")), 1)
            with open(os.path.join(d, "t.csv"), encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[1][0], 'Quote "me", please')


class OptionalDependencyTests(unittest.TestCase):

    def test_notification_and_sound_never_raise_without_backends(self):
        from services import notification_service, sound_service
        self.assertIn(notification_service.notify("t", "m", force=False), (True, False))
        sound_service.play_success()   # silently does nothing when disabled / unsupported


if __name__ == "__main__":
    unittest.main()
