"""Task manager."""
from __future__ import annotations

from datetime import date, timedelta
from tkinter import messagebox

import customtkinter as ctk

import config
from services import task_service
from ui import theme
from ui.pages_base import BasePage
from ui.widgets.components import Button, Card, Pill, empty_state, icon, label

PRIORITY_TOKEN = {"Urgent": "plum", "High": "danger", "Medium": "sun", "Low": "muted"}


def menu(parent, values, width=120, **kw) -> ctk.CTkOptionMenu:
    return ctk.CTkOptionMenu(parent, values=values, width=width, height=36, corner_radius=10,
                             fg_color=theme.pair("surface2"), button_color=theme.pair("surface3"),
                             button_hover_color=theme.pair("border"), text_color=theme.pair("text"),
                             dropdown_fg_color=theme.pair("surface2"), dropdown_text_color=theme.pair("text"),
                             dropdown_hover_color=theme.pair("surface3"), font=theme.font(12), **kw)


def entry(parent, placeholder="", width=0, **kw) -> ctk.CTkEntry:
    return ctk.CTkEntry(parent, placeholder_text=placeholder, height=36, corner_radius=10, border_width=1,
                        border_color=theme.pair("border"), fg_color=theme.pair("surface2"),
                        text_color=theme.pair("text"), font=theme.font(12), **({"width": width} if width else {}), **kw)


class TasksPage(BasePage):
    title = "Tasks"

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._search_job = None

        # ---- add form -----------------------------------------------------------
        form = Card(self)
        form.pack(fill="x", pady=(0, 10))
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(14, 6))
        self.title_entry = entry(row, "What needs doing?")
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.category = menu(row, config.CATEGORIES, 112)
        self.category.pack(side="left", padx=4)
        self.priority = menu(row, config.PRIORITIES, 104)
        self.priority.set("Medium")
        self.priority.pack(side="left", padx=4)
        self.due_entry = entry(row, "Due: YYYY-MM-DD", 150)
        self.due_entry.pack(side="left", padx=4)
        Button(row, "Add task", self.add_new_task, kind="primary", icon_name="plus", width=120).pack(side="left", padx=(8, 0))
        quick = ctk.CTkFrame(form, fg_color="transparent")
        quick.pack(fill="x", padx=14, pady=(0, 12))
        label(quick, "Quick due date:", 11, tone="muted").pack(side="left", padx=(2, 8))
        for text, days in (("Today", 0), ("Tomorrow", 1), ("In a week", 7)):
            Button(quick, text, lambda d=days: self._set_due(d), kind="ghost", width=90, height=28).pack(side="left", padx=3)
        self.form_error = label(quick, "", 11, tone="danger")
        self.form_error.pack(side="right", padx=6)
        self.title_entry.bind("<Return>", lambda e: self.add_new_task())
        self.due_entry.bind("<Return>", lambda e: self.add_new_task())

        # ---- filters ------------------------------------------------------------
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.search_entry = entry(bar, "Search tasks")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._debounced_load())
        self.status = ctk.CTkSegmentedButton(
            bar, values=["All", "Active", "Done"], command=lambda v: self.load_tasks(), height=34, corner_radius=10,
            font=theme.font(12, "bold"), fg_color=theme.pair("surface2"), unselected_color=theme.pair("surface2"),
            unselected_hover_color=theme.pair("surface3"), selected_color=theme.pair("tomato"),
            selected_hover_color=theme.pair("tomato_hi"), text_color=theme.pair("text"))
        self.status.set("Active")
        self.status.pack(side="left", padx=4)
        self.category_filter = menu(bar, ["All"] + config.CATEGORIES, 118, command=lambda v: self.load_tasks())
        self.category_filter.pack(side="left", padx=4)
        self.priority_filter = menu(bar, ["All"] + config.PRIORITIES, 108, command=lambda v: self.load_tasks())
        self.priority_filter.pack(side="left", padx=(4, 0))

        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

    # ----------------------------------------------------------------- lifecycle

    def on_show(self) -> None:
        self.load_tasks()

    def focus_new_task(self) -> None:
        self.title_entry.focus_set()

    def set_search(self, text: str) -> None:
        self.status.set("All")
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)
        self.load_tasks()

    def prefill_due(self, day: str) -> None:
        self.due_entry.delete(0, "end")
        self.due_entry.insert(0, day)
        self.title_entry.focus_set()

    # ------------------------------------------------------------------- actions

    def _set_due(self, days: int) -> None:
        self.prefill_due((date.today() + timedelta(days=days)).isoformat())

    def _debounced_load(self) -> None:
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(160, self.load_tasks)

    def add_new_task(self) -> None:
        try:
            task_service.add_task(self.title_entry.get(), self.category.get(), self.priority.get(), self.due_entry.get())
        except ValueError as error:
            self.form_error.configure(text=str(error))
            return
        self.form_error.configure(text="")
        self.title_entry.delete(0, "end")
        self.due_entry.delete(0, "end")
        self.priority.set("Medium")
        self.status.set("Active" if self.status.get() == "Done" else self.status.get())
        self.load_tasks()
        self.app.refresh_badges()
        self.app.toast("Task added", "success")

    def toggle_done(self, task_id: int, completed: bool) -> None:
        (task_service.reopen_task if completed else task_service.complete_task)(task_id)
        self.load_tasks()
        self.app.refresh_badges()
        if not completed:
            self.app.toast("Task completed", "success")

    def focus_task(self, task_id: int, title: str) -> None:
        self.app.pomodoro.set_current_task(task_id, title)
        self.app.show_page("Pomodoro")

    def delete_task(self, task_id: int, title: str) -> None:
        if not messagebox.askyesno("Delete task", f"Delete “{title}”? This can't be undone."):
            return
        task_service.delete_task(task_id)
        self.load_tasks()
        self.app.refresh_badges()
        self.app.toast("Task deleted", "info")

    # ------------------------------------------------------------------- listing

    def load_tasks(self) -> None:
        for widget in self.container.winfo_children():
            widget.destroy()
        rows = task_service.get_tasks(self.search_entry.get(), self.category_filter.get(),
                                      self.priority_filter.get(), self.status.get())
        if not rows:
            filtered = self.search_entry.get() or self.status.get() != "All"
            empty_state(self.container, "tasks", "No matching tasks" if filtered else "No tasks yet",
                        "Try a different filter." if filtered else
                        "Add your first task above, then press Focus to start a session on it.").pack(pady=20)
            return
        today = date.today().isoformat()
        for row in rows:
            self._row(row, today)

    def _row(self, task, today: str) -> None:
        task_id, title, category, priority, due, completed, pomodoros = task
        card = Card(self.container, corner_radius=14)
        card.pack(fill="x", pady=4, padx=2)
        done_token = "leaf" if completed else "border"
        check = ctk.CTkButton(card, text="", width=30, height=30, corner_radius=15, hover=False,
                              image=icon("check", 16, "on_tomato") if completed else None,
                              fg_color=theme.pair("leaf") if completed else "transparent",
                              border_width=2, border_color=theme.pair(done_token),
                              command=lambda i=task_id, c=bool(completed): self.toggle_done(i, c))
        check.pack(side="left", padx=(14, 10), pady=14)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, pady=10)
        font = ctk.CTkFont(family=theme.font(13)[0], size=13, weight="bold", overstrike=bool(completed))
        ctk.CTkLabel(body, text=title, font=font, anchor="w",
                     text_color=theme.pair("muted" if completed else "text")).pack(anchor="w")
        meta = ctk.CTkFrame(body, fg_color="transparent")
        meta.pack(anchor="w", pady=(4, 0))
        Pill(meta, priority, PRIORITY_TOKEN.get(priority, "muted")).pack(side="left")
        label(meta, category, 11, tone="muted").pack(side="left", padx=(10, 0))
        if due:
            overdue = not completed and due < today
            label(meta, ("Overdue · " if overdue else "Due ") + due, 11, "bold" if overdue else "normal",
                  tone="danger" if overdue else "muted").pack(side="left", padx=(10, 0))
        if pomodoros:
            label(meta, f"{pomodoros} session{'s' if pomodoros != 1 else ''}", 11, tone="muted").pack(side="left", padx=(10, 0))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=10)
        if not completed:
            Button(actions, "Focus", lambda i=task_id, t=title: self.focus_task(i, t), kind="ghost",
                   icon_name="play", width=88, height=32).pack(side="left", padx=2)
        Button(actions, "", lambda t=task: self.edit_task(t), kind="ghost", icon_name="edit", width=34, height=32).pack(side="left", padx=2)
        Button(actions, "", lambda i=task_id, t=title: self.delete_task(i, t), kind="danger", icon_name="trash", width=34, height=32).pack(side="left", padx=2)

    # --------------------------------------------------------------------- edit

    def edit_task(self, task) -> None:
        task_id, title, category, priority, due, completed, pomodoros = task
        win = ctk.CTkToplevel(self)
        win.title("Edit task")
        win.geometry("440x360")
        win.resizable(False, False)
        win.configure(fg_color=theme.pair("surface"))
        win.transient(self.winfo_toplevel())
        self.after(150, lambda: self._modal(win))

        label(win, "Edit task", 18, "bold").pack(anchor="w", padx=24, pady=(22, 12))
        title_entry = entry(win)
        title_entry.pack(fill="x", padx=24, pady=5)
        title_entry.insert(0, title)
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=5)
        cat = menu(row, config.CATEGORIES, 190)
        cat.set(category)
        cat.pack(side="left")
        pri = menu(row, config.PRIORITIES, 190)
        pri.set(priority)
        pri.pack(side="right")
        due_entry = entry(win, "Due date: YYYY-MM-DD")
        due_entry.pack(fill="x", padx=24, pady=5)
        due_entry.insert(0, due or "")
        error = label(win, "", 11, tone="danger", anchor="w")
        error.pack(fill="x", padx=26)

        def save():
            try:
                task_service.update_task(task_id, title_entry.get(), cat.get(), pri.get(), due_entry.get())
            except ValueError as exc:
                error.configure(text=str(exc))
                return
            win.destroy()
            self.load_tasks()
            self.app.toast("Task updated", "success")

        buttons = ctk.CTkFrame(win, fg_color="transparent")
        buttons.pack(side="bottom", fill="x", padx=24, pady=20)
        Button(buttons, "Save changes", save, kind="primary", width=140).pack(side="right")
        Button(buttons, "Cancel", win.destroy, kind="ghost", width=100).pack(side="right", padx=8)
        title_entry.bind("<Return>", lambda e: save())

    @staticmethod
    def _modal(win) -> None:
        try:
            win.grab_set()
            win.focus_force()
        except Exception:
            pass
