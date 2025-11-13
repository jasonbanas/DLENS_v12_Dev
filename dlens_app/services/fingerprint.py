import re
from bs4 import BeautifulSoup
import hashlib

def dom_fingerprint(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h2s = [re.sub(r"\s+", " ", h.get_text(strip=True)) for h in soup.find_all("h2")]
    sig = "|".join(h2s)
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]
