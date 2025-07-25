import json

import sentry_sdk


def send_alert(level: str, message: str, details: dict = None):
    """
    Sends an alert. In production, this would integrate with PagerDuty, Sentry, etc.
    For now, it prints a structured log to the console.
    """
    alert_payload = {
        "level": level.upper(),
        "message": message,
        "details": details or {}
    }
    # The [ALERT] prefix makes it easy to find and filter in logs
    print(f"[ALERT] {json.dumps(alert_payload)}")
    # --- SEND TO SENTRY ---
    with sentry_sdk.push_scope() as scope:
        scope.set_level(level)
        for key, value in (details or {}).items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message)