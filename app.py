from ui.main_window import MainWindow
from services.task_service import initialize_tasks

initialize_tasks()

def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()