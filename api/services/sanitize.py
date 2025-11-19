import re

def sanitize_ticker(v: str) -> str:
    """
    Ensures ticker is uppercase and valid format.
    Allowed: A–Z, 0–9, -, .  (max 12 chars)
    """
    if not v:
        raise ValueError("Ticker is required")

    v = v.upper().strip()

    if not re.fullmatch(r"[A-Z0-9\-.]{1,12}", v):
        raise ValueError(f"Invalid ticker format: {v}")

    return v


def clamp_years(v) -> int:
    """
    Converts input to int and clamps between 1–20 years.
    """
    try:
        n = int(v)
    except:
        n = 6

    # clamp 1–20
    return max(1, min(20, n))
