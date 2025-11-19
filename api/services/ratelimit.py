# Simple rate limiter placeholder for DLENS v12
# Always allows all requests

def allow(user_id: str, route: str) -> bool:
    """
    Rate limit handler (dev mode).
    Always returns True so every request is allowed.
    Replace with Redis or DB-based RL if needed.
    """
    return True
