# Changelog

## 2.0.0

A ground-up refresh of the interface and a rewrite of the core, with the same data and the same idea.

### Added
- Dock navigation (spring magnification, hop on click, badges, tooltips, right-click menus), ported from React Bits' `Dock`.
- `RotatingText` (slide / flip / blur / scale / drop, stagger, highlight block), ported from React Bits, used for page titles and the dashboard headline.
- Cursor animation on Windows: trail, magnetic ring, click ripples. Verified click-through; disabled automatically if it can't be confirmed.
- Timer ring with phase colours, glow, confetti, live window-title countdown, session dots, task selector and keyboard shortcuts.
- Native animated bar / donut charts and a 12-week activity heatmap (Matplotlib removed).
- Native month calendar with priority dots and click-to-add (`tkcalendar` removed).
- `Ctrl + K` command palette; `Ctrl + 1…8` and `Ctrl + N` shortcuts.
- Light theme, "System" theme, persistent settings, "Animations" and "Cursor effects" switches, daily goal, auto-start toggle.
- Task improvements: quick due dates, reopen completed tasks, status / category / priority filters, session counts.
- Achievements with progress bars; best-streak tracking.
- Break sessions are now logged and shown in History; sessions link to the selected task.
- Export tasks as CSV; open data folder; reset data.
- Test suite (62 tests), headless UI harness, `tools/render_previews.py`, `CHANGELOG.md`.

### Changed
- One database layer (`services/db.py`) with in-place migrations for v1 databases.
- Database path no longer depends on the working directory; packaged builds use `%APPDATA%/FocusFlow`.
- Insights are described honestly as local rules (no AI service).
- Dashboard "focus minutes" is the real sum of finished work minutes (was `pomodoros × 25`).

### Fixed
- **Timer ran at double speed after pause/resume** (a second countdown loop was started each time). Replaced by a monotonic-clock state machine.
- Timer ignored changed durations until reset; the sound and notification switches were saved but never consulted.
- Statistics filter (Today / Week / Month) had no effect; the export button was re-created on every refresh.
- Priority sorting was alphabetical (Medium > Low > High); now Urgent → Low.
- "Today" / "This Week" history filters used UTC while sessions are stored in local time.
- An invalid due date crashed the calendar later; dates are now validated on entry.
- App crashed at start on macOS/Linux (`winsound`) or without `plyer`; both are now optional.
- `winsound.Beep` froze the window for half a second; sounds now play on a worker thread.
- Weekly chart skipped days without sessions; empty days now appear as zero.
- Several modules created a `sessions` table with conflicting schemas.
- Calendar did not refresh after task changes.
- Nested same-quote f-strings required Python 3.12+; the code now runs on 3.10+.

### Removed
- Sidebar, `stat_card`, `productivity_chart`, empty `timer_page` (replaced by the dock and new widgets).
- Dependencies: `matplotlib`, `tkcalendar`.
