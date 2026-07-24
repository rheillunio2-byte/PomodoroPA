from services.settings_service import load_settings

class PomodoroTimer:

    def __init__(self):

        work, short, long_break, interval = load_settings()

        self.work_minutes = work

        self.break_minutes = short

        self.long_break_minutes = long_break

        self.long_break_every = interval

        self.seconds_left = self.work_minutes * 60

        self.running = False

        self.paused = False

    def reset(self):

        self.running = False

        self.paused = False

        self.seconds_left = self.work_minutes * 60

    def pause(self):

        self.paused = True

    def resume(self):

        self.paused = False

    def start(self):

        self.running = True