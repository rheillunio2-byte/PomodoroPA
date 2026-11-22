"""Desktop notifications (optional).

``plyer`` is imported lazily: if it is not installed, or the platform has no
notification backend, ``notify`` quietly returns ``False`` and the in-app toast
is the only feedback.  The call is made on a worker thread because some
backends block for a moment.
"""
from __future__ import annotations

import threading

import config
from services.settings_service import get_settings


def is_available() -> bool:
    try:
        import plyer  # noqa: F401
        return True
    except Exception:
        return False


def notify(title: str, message: str, force: bool = False) -> bool:
    """Show a system notification if the user enabled them.  Never raises."""
    try:
        if not force and not get_settings()["notifications"]:
            return False
        from plyer import notification
    except Exception:
        return False

    def _send() -> None:
        try:
            notification.notify(title=title, message=message,
                                app_name=config.APP_NAME, timeout=8)
        except Exception:
            pass  # a missing backend must never take the app down

    threading.Thread(target=_send, daemon=True).start()
    return True
