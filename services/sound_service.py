import winsound


def play_success():

    winsound.MessageBeep()


def play_error():

    winsound.Beep(700, 300)


def play_break():

    winsound.Beep(1200, 500)