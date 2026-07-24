import customtkinter as ctk
from tkinter import messagebox

from services.task_service import (
    add_task,
    get_tasks,
    complete_task,
    delete_task,
    update_task
)


class TasksPage(ctk.CTkFrame):

    def __init__(self, parent, app):

        super().__init__(parent)

        self.app = app

        # ======================================================
        # TITLE
        # ======================================================

        title = ctk.CTkLabel(
            self,
            text='📝 Task Manager',
            font=('Segoe UI', 30, 'bold')
        )

        title.pack(pady=(20, 15))

        # ======================================================
        # ADD TASK AREA
        # ======================================================

        input_frame = ctk.CTkFrame(self)

        input_frame.pack(
            fill='x',
            padx=20,
            pady=(0, 10)
        )

        self.title_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text='Task title...'
        )

        self.title_entry.pack(
            side='left',
            expand=True,
            fill='x',
            padx=10,
            pady=10
        )

        self.category = ctk.CTkComboBox(
            input_frame,
            values=['Study', 'Work', 'Personal', 'Health'],
            width=140
        )

        self.category.set('Study')

        self.category.pack(side='left', padx=5)

        self.priority = ctk.CTkComboBox(
            input_frame,
            values=['Low', 'Medium', 'High', 'Urgent'],
            width=140
        )

        self.priority.set('Medium')

        self.priority.pack(side='left', padx=5)

        self.date_entry = ctk.CTkEntry(
            input_frame,
            width=140,
            placeholder_text='YYYY-MM-DD'
        )

        self.date_entry.pack(side='left', padx=5)

        add_button = ctk.CTkButton(
            input_frame,
            text='➕ Add Task',
            width=120,
            command=self.add_new_task
        )

        add_button.pack(side='left', padx=10)

        # ======================================================
        # SEARCH & FILTERS
        # ======================================================

        filter_frame = ctk.CTkFrame(self)

        filter_frame.pack(
            fill='x',
            padx=20,
            pady=(0, 10)
        )

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text='🔍 Search tasks...'
        )

        self.search_entry.pack(
            side='left',
            fill='x',
            expand=True,
            padx=10,
            pady=10
        )

        self.search_entry.bind(
            '<KeyRelease>',
            lambda event: self.load_tasks()
        )

        self.category_filter = ctk.CTkComboBox(
            filter_frame,
            values=['All', 'Study', 'Work', 'Personal', 'Health'],
            width=130
        )

        self.category_filter.set('All')

        self.category_filter.pack(side='left', padx=5)

        self.category_filter.configure(
            command=lambda value: self.load_tasks()
        )

        self.priority_filter = ctk.CTkComboBox(
            filter_frame,
            values=['All', 'Low', 'Medium', 'High', 'Urgent'],
            width=130
        )

        self.priority_filter.set('All')

        self.priority_filter.pack(side='left', padx=5)

        self.priority_filter.configure(
            command=lambda value: self.load_tasks()
        )

        # ======================================================
        # TASK LIST
        # ======================================================

        self.task_container = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent'
        )

        self.task_container.pack(
            fill='both',
            expand=True,
            padx=20,
            pady=(5, 20)
        )

        self.load_tasks()

    # ======================================================
    # ADD TASK
    # ======================================================

    def add_new_task(self):

        title = self.title_entry.get().strip()

        if title == '':
            messagebox.showwarning(
                'Missing Title',
                'Please enter a task title.'
            )
            return

        add_task(
            title,
            self.category.get(),
            self.priority.get(),
            self.date_entry.get()
        )

        self.title_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')

        self.category.set('Study')
        self.priority.set('Medium')

        self.load_tasks()

    # ======================================================
    # LOAD TASKS
    # ======================================================

    def load_tasks(self):

        for widget in self.task_container.winfo_children():
            widget.destroy()

        tasks = get_tasks()

        search = self.search_entry.get().lower()
        selected_category = self.category_filter.get()
        selected_priority = self.priority_filter.get()

        priority_colors = {
            'Low': '#808080',
            'Medium': '#f39c12',
            'High': '#e74c3c',
            'Urgent': '#8e44ad'
        }

        visible = 0

        for task in tasks:

            task_id, title, category, priority, due, completed, pomodoros = task

            # ---------------- SEARCH ----------------

            if search and search not in title.lower():
                continue

            # ---------------- CATEGORY FILTER ----------------

            if selected_category != 'All' and category != selected_category:
                continue

            # ---------------- PRIORITY FILTER ----------------

            if selected_priority != 'All' and priority != selected_priority:
                continue

            visible += 1

            # ==================================================
            # CARD
            # ==================================================

            card = ctk.CTkFrame(
                self.task_container,
                corner_radius=15
            )

            card.pack(
                fill='x',
                padx=8,
                pady=8
            )

            # ---------------- TOP ----------------

            top = ctk.CTkFrame(
                card,
                fg_color='transparent'
            )

            top.pack(
                fill='x',
                padx=15,
                pady=(12, 5)
            )

            title_label = ctk.CTkLabel(
                top,
                text=f'{'✅' if completed else '⭕'} {title}',
                font=('Segoe UI', 18, 'bold')
            )

            title_label.pack(side='left')

            badge = ctk.CTkLabel(
                top,
                text=priority.upper(),
                width=90,
                corner_radius=8,
                fg_color=priority_colors.get(priority, '#808080')
            )

            badge.pack(side='right')

            # ---------------- INFO ----------------

            info = ctk.CTkLabel(
                card,
                text=(
                    f"📂 {category}"
                    f"     📅 {due}"
                    f"     🍅 {pomodoros}"
                ),
                font=("Segoe UI",13)
            )

            info.pack(anchor='w', padx=15)

            # ---------------- POMODOROS ----------------

            pomodoro_label = ctk.CTkLabel(
                card,
                text=f'🍅 Pomodoros: {pomodoros}',
                font=('Segoe UI', 13, 'bold'),
                text_color='#16a34a'
            )

            pomodoro_label.pack(anchor='w', padx=15, pady=(2, 0))

            # ---------------- BUTTONS ----------------

            button_frame = ctk.CTkFrame(
                card,
                fg_color='transparent'
            )

            button_frame.pack(
                anchor='w',
                padx=15,
                pady=(10, 12)
            )

            # COMPLETE BUTTON

            if completed == 0:

                ctk.CTkButton(
                    button_frame,
                    text="🍅 Focus",
                    width=100,
                    fg_color="#16a34a",
                    hover_color="#15803d",
                    command=lambda i=task_id, t=title: self.focus_task(i, t)
                ).pack(
                    side="left",
                    padx=(0,5)
                )

                ctk.CTkButton(
                    button_frame,
                    text="✓ Complete",
                    width=120,
                    command=lambda i=task_id: self.complete_task(i)
                ).pack(
                    side="left",
                    padx=(0,5)
                )

            # EDIT BUTTON

            ctk.CTkButton(
                button_frame,
                text='✏ Edit',
                width=100,
                fg_color='#2563eb',
                hover_color='#1d4ed8',
                command=lambda t=task: self.edit_task(t)
            ).pack(
                side='left',
                padx=5
            )

            # DELETE BUTTON

            ctk.CTkButton(
                button_frame,
                text='🗑 Delete',
                width=100,
                fg_color='#c0392b',
                hover_color='#922b21',
                command=lambda i=task_id: self.delete_task(i)
            ).pack(side='left')

        # ======================================================
        # EMPTY STATE
        # ======================================================

        if visible == 0:

            ctk.CTkLabel(
                self.task_container,
                text='No matching tasks found.',
                font=('Segoe UI', 18)
            ).pack(pady=30)

    # ======================================================
    # FOCUS TASK
    # ======================================================

    def focus_task(self, task_id, title):

        pomodoro = self.app.pages["Pomodoro"]

        pomodoro.set_current_task(
            task_id,
            title
        )

        self.app.show_page("Pomodoro")

    # ======================================================
    # COMPLETE
    # ======================================================

    def complete_task(self, task_id):

        complete_task(task_id)

        self.load_tasks()

    # ======================================================
    # DELETE
    # ======================================================

    def delete_task(self, task_id):

        if not messagebox.askyesno(
            'Delete Task',
            'Are you sure you want to delete this task?'
        ):
            return

        delete_task(task_id)

        self.load_tasks()

    # ======================================================
    # EDIT
    # ======================================================

    def edit_task(self, task):

        task_id, title, category, priority, due, completed, pomodoros = task

        window = ctk.CTkToplevel(self)

        window.title('Edit Task')
        window.geometry('420x330')
        window.grab_set()

        ctk.CTkLabel(
            window,
            text='Edit Task',
            font=('Segoe UI', 22, 'bold')
        ).pack(pady=15)

        title_entry = ctk.CTkEntry(window)

        title_entry.pack(fill='x', padx=25, pady=10)

        title_entry.insert(0, title)

        category_box = ctk.CTkComboBox(
            window,
            values=['Study', 'Work', 'Personal', 'Health']
        )

        category_box.pack(fill='x', padx=25, pady=10)

        category_box.set(category)

        priority_box = ctk.CTkComboBox(
            window,
            values=['Low', 'Medium', 'High', 'Urgent']
        )

        priority_box.pack(fill='x', padx=25, pady=10)

        priority_box.set(priority)

        date_entry = ctk.CTkEntry(window)

        date_entry.pack(fill='x', padx=25, pady=10)

        date_entry.insert(0, due)

        def save():

            update_task(
                task_id,
                title_entry.get(),
                category_box.get(),
                priority_box.get(),
                date_entry.get()
            )

            window.destroy()

            self.load_tasks()

        ctk.CTkButton(
            window,
            text='💾 Save Changes',
            command=save
        ).pack(pady=20)