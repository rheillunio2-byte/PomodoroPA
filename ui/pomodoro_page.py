import customtkinter as ctk

from services.pomodoro_service import PomodoroTimer
from services.session_service import save_session
from services.notification_service import notify
from services.sound_service import play_success
from services.task_service import add_pomodoro
from services.settings_service import load_settings

class PomodoroPage(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(parent)

        # ==========================================
        # TIMER ENGINE
        # ==========================================

        self.timer = PomodoroTimer()

        self.session_count = 0

        self.mode = "Work"

        self.current_task_id = None
        self.current_task_title = "No task selected"

        # ==========================================
        # TITLE
        # ==========================================

        title = ctk.CTkLabel(
            self,
            text="Pomodoro Timer",
            font=("Segoe UI", 32, "bold")
        )

        title.pack(
            pady=(25, 10)
        )

        # ==========================================
        # MODE LABEL
        # ==========================================

        self.mode_label = ctk.CTkLabel(
            self,
            text="🍅 Work Session",
            font=("Segoe UI", 22, "bold")
        )

        self.mode_label.pack(
            pady=(10, 5)
        )

        # ==========================================
        # CURRENT TASK
        # ==========================================

        self.task_label = ctk.CTkLabel(
            self,
            text="📋 Current Task: None",
            font=("Segoe UI", 18)
        )

        self.task_label.pack(
            pady=(5, 15)
        )

        # ==========================================
        # TIMER
        # ==========================================

        self.timer_label = ctk.CTkLabel(
            self,
            text="25:00",
            font=("Segoe UI", 72, "bold")
        )

        self.timer_label.pack(
            pady=30
        )

        # ==========================================
        # STATUS
        # ==========================================

        self.status_label = ctk.CTkLabel(
            self,
            text="Ready to focus.",
            font=("Segoe UI", 15)
        )

        self.status_label.pack()

        # ==========================================
        # BUTTONS
        # ==========================================

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        button_frame.pack(
            pady=25
        )

        self.start_button = ctk.CTkButton(
            button_frame,
            text="▶ Start",
            width=120,
            command=self.start_timer
        )

        self.start_button.pack(
            side="left",
            padx=5
        )

        self.pause_button = ctk.CTkButton(
            button_frame,
            text="⏸ Pause",
            width=120,
            command=self.pause_timer
        )

        self.pause_button.pack(
            side="left",
            padx=5
        )

        self.resume_button = ctk.CTkButton(
            button_frame,
            text="▶ Resume",
            width=120,
            command=self.resume_timer
        )

        self.resume_button.pack(
            side="left",
            padx=5
        )

        self.reset_button = ctk.CTkButton(
            button_frame,
            text="🔄 Reset",
            width=120,
            command=self.reset_timer
        )

        self.reset_button.pack(
            side="left",
            padx=5
        )

        # ==========================================
        # SESSION INFO
        # ==========================================

        info_frame = ctk.CTkFrame(self)

        info_frame.pack(
            fill="x",
            padx=40,
            pady=20
        )

        self.completed_label = ctk.CTkLabel(
            info_frame,
            text="Completed Sessions: 0",
            font=("Segoe UI", 18)
        )

        self.completed_label.pack(
            pady=10
        )

        self.update_clock()

    # ==========================================
    # START TIMER
    # ==========================================

    def start_timer(self):

        if self.timer.running:
            return

        self.timer.start()

        self.status_label.configure(
            text="Focus session in progress..."
        )

        self.countdown()

    # ==========================================
    # PAUSE TIMER
    # ==========================================

    def pause_timer(self):

        if not self.timer.running:
            return

        self.timer.pause()

        self.status_label.configure(
            text="Timer paused."
        )

    # ==========================================
    # RESUME TIMER
    # ==========================================

    def resume_timer(self):

        if not self.timer.running:
            return

        self.timer.resume()

        self.status_label.configure(
            text="Focus session resumed."
        )

        self.countdown()

    # ==========================================
    # RESET TIMER
    # ==========================================

    def reset_timer(self):

        self.timer.reset()

        work, short, long_break, interval = load_settings()

        self.timer.work_minutes = work

        self.timer.break_minutes = short

        self.timer.long_break_minutes = long_break

        self.timer.long_break_every = interval

        self.timer.seconds_left = work * 60

        self.mode = "Work"

        self.mode_label.configure(
            text="🍅 Work Session"
        )

        self.status_label.configure(
            text="Timer reset."
        )

        self.update_clock()

    # ==========================================
    # UPDATE CLOCK
    # ==========================================

    def update_clock(self):

        minutes = self.timer.seconds_left // 60
        seconds = self.timer.seconds_left % 60

        self.timer_label.configure(
            text=f"{minutes:02}:{seconds:02}"
        )

    # ==========================================
    # COUNTDOWN
    # ==========================================

    def countdown(self):

        if not self.timer.running:
            return

        if self.timer.paused:

            self.after(
                1000,
                self.countdown
            )

            return

        self.update_clock()

        if self.timer.seconds_left > 0:

            self.timer.seconds_left -= 1

            self.after(
                1000,
                self.countdown
            )

        else:

            self.timer.running = False

            self.session_finished()

    # ==========================================
    # SESSION FINISHED
    # ==========================================

    def session_finished(self):

        if self.mode == "Work":

            save_session(
                self.timer.work_minutes,
                self.mode
            )

            play_success()

            notify(
                "Pomodoro Complete",
                "Great work! Time for a break."
            )

            # --------------------------------------
            # Add Pomodoro to current task
            # --------------------------------------

            if self.current_task_id is not None:

                add_pomodoro(
                    self.current_task_id
                )

            self.session_count += 1

            self.completed_label.configure(
                text=f"Completed Sessions: {self.session_count}"
            )

            if self.session_count % self.timer.long_break_every == 0:

                self.mode = "Long Break"

                self.mode_label.configure(
                    text="🌙 Long Break"
                )

                self.timer.seconds_left = (
                    self.timer.long_break_minutes * 60
                )

            else:

                self.mode = "Short Break"

                self.mode_label.configure(
                    text="☕ Short Break"
                )

                self.timer.seconds_left = (
                    self.timer.break_minutes * 60
                )

            self.status_label.configure(
                text="Work session completed!"
            )

        else:

            notify(
                "Break Finished",
                "Let's get back to work!"
            )

            play_success()

            self.mode = "Work"

            self.mode_label.configure(
                text="🍅 Work Session"
            )

            self.timer.seconds_left = (
                self.timer.work_minutes * 60
            )

            self.status_label.configure(
                text="Break finished. Time to focus!"
            )

        self.update_clock()

        try:

            self.master.master.pages["Tasks"].load_tasks()

        except Exception:

            pass

        self.start_next_session()

    # ==========================================
    # START NEXT SESSION
    # ==========================================

    def start_next_session(self):

        self.timer.running = False

        self.timer.paused = False

        self.start_timer()


    # ==========================================
    # SET CURRENT TASK
    # ==========================================

    def set_current_task(self, task_id, title):

        self.current_task_id = task_id

        self.current_task_title = title

        self.task_label.configure(
            text=f"📋 Current Task: {title}"
        )

