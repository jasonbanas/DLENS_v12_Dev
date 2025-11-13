import hmac
import hashlib
import time
import base64
import os

SECRET = os.getenv("REPORT_LINK_SECRET", "changeme")


def sign_path(path: str, exp_seconds: int = 3600) -> str:
    """Return a URL-safe signed path with expiration timestamp."""
    exp = int(time.time()) + exp_seconds
    data = f"{path}|{exp}".encode()
    sig = hmac.new(SECRET.encode(), data, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{path}?exp={exp}&sig={token}"


def verify(path: str, exp: int, sig: str) -> bool:
    """Verify that the provided path signature is valid and not expired."""
    data = f"{path}|{exp}".encode()
    expected = base64.urlsafe_b64encode(
        hmac.new(SECRET.encode(), data, hashlib.sha256).digest()
    ).decode().rstrip("=")
    return exp >= int(time.time()) and hmac.compare_digest(expected, sig)
