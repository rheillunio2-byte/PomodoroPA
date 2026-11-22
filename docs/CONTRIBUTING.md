# Contributing to FocusFlow

Thank you for your interest in contributing to **FocusFlow**! Bug fixes, features, design improvements and documentation are all welcome.

## Quick start

```bash
git clone https://github.com/<your-username>/PomodoroPA.git
cd PomodoroPA
python -m venv .venv && .venv\Scripts\activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py                                      # run the app
python -m unittest discover -s tests -t .          # run the tests (no display needed)
```

Python **3.10+**. Use a feature branch (`git checkout -b feature/your-change`), keep commits focused, and open a pull request describing **what** changed, **why**, and, for UI work, **screenshots or a short screen recording**.

---

## How the code is organised

| Layer | Folder | Rule |
|-------|--------|------|
| Logic & data | `services/` | **Never import `tkinter`/`customtkinter`.** All SQL goes through `services/db.py`. |
| Rendering & physics | `ui/engine/` | **Pure Python + Pillow, no Tk.** This is what makes the animations testable. |
| Tk widgets | `ui/widgets/` | Thin wrappers that put engine output on a canvas, plus reusable CustomTkinter components. |
| Pages & shell | `ui/*_page.py`, `ui/main_window.py` | Compose widgets and call services. |

If you can write something as a function from numbers to an image or a number, put it in `ui/engine/` and test it there.

### Database changes
* Add new columns to `_MIGRATIONS` in `services/db.py` (never edit an existing `CREATE TABLE` only: users already have databases). `init_db()` upgrades them in place.
* Add a test that opens an old-layout database (see `test_migrates_a_v1_database_in_place`).

### Adding a page
1. Create `ui/your_page.py` with a class extending `BasePage` (`on_show()` reloads data).
2. Register it in `PAGES` in `ui/main_window.py` (name → class, dock icon name). It appears in the dock, the header title, the command palette and `Ctrl + N` shortcuts automatically.
3. Add an icon to `ui/engine/icons.py` if needed (24 × 24 grid; run `tools/render_previews.py` to see it).

### Adding a dock item or menu
Items are `DockItem` objects in `MainWindow._build_dock`. `menu` is a list of `(label, callback)` pairs (or `None` for a separator) shown on right-click.

---

## UI guidelines

**Colours**
* Never hard-code colours. Use palette tokens through `theme.pair("token")` (CustomTkinter) or `theme.c("token")` (canvases). Tokens live in `ui/engine/palette.py`.
* Canvases extend `ThemedCanvas` so they redraw when the theme changes.
* Colour carries meaning: tomato = focus, green = short break, blue = long break.
* `tests/test_engine.py` enforces WCAG AA contrast for text colours in **both** themes. If you add or change a colour and that test fails, fix the colour, not the test.

**Motion**
* Animate state changes the user caused (hover, navigation, a session finishing). Don't add decorative loops.
* Use `ui.anim.tween` / `ui.anim.FrameLoop`; they respect Settings → *Animations*. Code that bypasses them must check `anim.enabled()`.
* Time-based, not frame-based: use the `dt` you are given.

**CustomTkinter gotchas**
* Its constructors **reject unknown keyword arguments** (for example `CTkLabel(justify=…)` or `padx=…` raise `ValueError`). `tests/fake_tk.py` enforces the real signatures, so the smoke tests will catch this. Use `components.label(...)` which handles `justify` safely.
* Don't name attributes after Tk methods (`scale`, `bind`, `grid`, `config`…). We use `self.dpi`, not `self.scale`.
* Don't pass `width=0` to buttons; `components.Button` picks sensible sizes.
* Canvas widgets can't use `(light, dark)` colour pairs: use `theme.c()` and `ThemedCanvas`.

**Text**
* Sentence case for labels and buttons; no ALL-CAPS headings.
* Error messages say what to do next ("Use the format YYYY-MM-DD…"), not just what failed.

---

## Testing

```bash
python -m unittest discover -s tests -t .
```

* `tests/test_services.py`: services against a temporary database (use `DatabaseTestCase`).
* `tests/test_engine.py`: palette contrast, motion, Dock/RotatingText engines and renderers.
* `tests/test_ui_smoke.py`: headless walk through the whole UI using `tests/fake_tk.py`. Add a case when you add a page or a user flow.

The fake Tk records calls; it can't judge appearance. For visual changes, **run the app** and (for components) check `python tools/render_previews.py`.

Please test on your own platform and say which one in your PR. Windows-only code (the cursor overlay) must degrade to a no-op elsewhere.

---

## Reporting bugs

Open a GitHub Issue with:

* A clear description and the steps to reproduce
* Expected vs. actual behaviour
* Screenshots or a recording (if visual)
* Python version, OS and display scaling (for example "Windows 11, 150%")
* Any traceback shown in the terminal

## Suggesting features

Describe the problem it solves, who benefits, and (optionally) how you'd build it. Ideas we'd love help with: PDF/Excel export, focus-music integration, weekly reports, goal and habit tracking, cloud sync.

---

## Pull request checklist

* ✔ `python -m unittest discover -s tests -t .` passes
* ✔ The app starts and the affected pages work (light **and** dark theme)
* ✔ New colours use palette tokens; new animations respect the *Animations* setting
* ✔ Database changes come with a migration and a test
* ✔ README / CHANGELOG updated if behaviour changed
* ✔ Clear commit messages

## License

By contributing to **FocusFlow**, you agree that your contributions will be licensed under the project's **MIT License**.

Thank you for helping improve FocusFlow!
