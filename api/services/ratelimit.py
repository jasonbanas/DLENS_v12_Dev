import time

BUCKET, WINDOW, MAX = {}, 60, 10  # store timestamps, 60s window, 10 max requests

def allow(user_id: str, route: str) -> bool:
    """
    Return True if the request is allowed, False if rate-limited.
    Allows up to MAX requests per (user_id, route) within WINDOW seconds.
    """
    now = time.time()
    key = (user_id, route)

    # Keep only timestamps within the current window
    arr = [t for t in BUCKET.get(key, []) if now - t < WINDOW]

    if len(arr) >= MAX:
        BUCKET[key] = arr  # update pruned timestamps
        return False

    arr.append(now)
    BUCKET[key] = arr
    return True
