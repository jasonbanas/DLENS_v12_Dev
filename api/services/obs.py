import datetime

def log_event(event: str, **kwargs):
    """
    Simple event logger for DLENS backend.
    Prints clean JSON-like logs to terminal for debugging.
    """
    timestamp = datetime.datetime.utcnow().isoformat()

    log_data = {
        "timestamp": timestamp,
        "event": event,
        "details": kwargs
    }

    print(f"[DLENS_LOG] {log_data}")
