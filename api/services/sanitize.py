import re

def sanitize_ticker(v: str) -> str:
    """Validate and normalize a stock ticker symbol."""
    v = (v or "").upper()
    if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
        raise ValueError("Invalid ticker")
    return v


def clamp_years(v) -> int:
    """Clamp a numeric input to the range 1–20, defaulting to 6 if invalid."""
    try:
        n = int(v)
    except Exception:
        n = 6
    return max(1, min(20, n))
