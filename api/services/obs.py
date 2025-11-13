import json
import time
import logging

log = logging.getLogger("dlens")

def log_event(event, **kw):
    """Log a structured JSON event with a timestamp."""
    kw.setdefault("ts", int(time.time()))
    kw.setdefault("event", event)
    log.info(json.dumps(kw))
