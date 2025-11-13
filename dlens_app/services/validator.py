# api/services/validator.py
from bs4 import BeautifulSoup
import re

# -----------------------------------------------------
# DLENS Spotlight v12 Gold — HTML Validator (Python)
# -----------------------------------------------------
# Returns: (ok: bool, errors: list[str], meta: dict)

def validate(html: str):
    errors = []
    meta = {}

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception as e:
        return False, [f"Invalid HTML parse: {e}"], meta

    body_text = soup.get_text(" ", strip=True)

    # ---------- 1) Basic sanity ----------
    if not soup.html or not soup.body:
        errors.append("Missing <html> or <body> tags.")

    title = (soup.title.string or "").strip() if soup.title else ""
    if not re.search(r"DLENS\s+Disruptor\s+Spotlight", title, re.I):
        errors.append("Missing or incorrect <title> (must include 'DLENS Disruptor Spotlight').")

    # ---------- 2) TradingView widget ----------
    if not soup.find("script", src=re.compile("tradingview.com", re.I)):
        errors.append("TradingView script not found.")

    # ---------- 3) DUU line ----------
    duu_re = re.compile(
        r"DUU\s*Score:\s*[0-9](?:\.[0-9])?\s*/\s*10\s*→\s*DUU\s*\(Most.?Likely\s+Price,\s*[0-9]{1,2}y\):"
        r"\s*\$[0-9][0-9,]*\.\d{2}\s*\(=\s*[0-9]+(?:\.\d+)?×\s*CSP\s*\$[0-9][0-9,]*\.\d{2}\s*≈\s*[0-9]+%\)"
        r"\s*•\s*Probability:\s*[0-9]{1,3}%",
        re.I,
    )
    if not duu_re.search(body_text):
        errors.append("DUU inline line missing or malformed.")

    # ---------- 4) CSP two-source ----------
    if not re.search(r"(Yahoo|Bloomberg|NASDAQ|NYSE|Reuters).*(Yahoo|Bloomberg|NASDAQ|NYSE|Reuters)", body_text, re.I):
        errors.append("CSP (2-source) anchors missing.")
    if not re.search(r"\$[0-9][0-9,]*\.\d{2}.*\$[0-9][0-9,]*\.\d{2}", body_text):
        errors.append("CSP (2-source) missing two numeric values.")
    if not re.search(r"(AM|PM|UTC|CET|PST|EDT|GMT)", body_text, re.I):
        errors.append("CSP timestamp not detected.")

    # ---------- 5) Required sections (by <h2>) ----------
    required_sections = [
        "Disruption Lens",
        "What is the company",
        "Why now",
        "Feasibility",
        "Founder Execution Premium",
        "Peer Comparison",
        "Truth Audit",
        "Metrics to Watch",
        "Milestones",
        "Risks",
        "What would change",
        "Decision-Ready Conclusion",
        "Compliance Checklist",
    ]
    headings = [h.get_text(strip=True) for h in soup.find_all("h2")]
    for section in required_sections:
        if not any(section.lower() in h.lower() for h in headings):
            errors.append(f"Missing section: {section}")

    # ---------- 6) Peer table ----------
    peer = None
    for h2 in soup.find_all("h2"):
        if "peer" in h2.get_text().lower():
            peer = h2.find_next("table")
            break
    if not peer:
        errors.append("Peer Comparison table not found.")
    else:
        headers = [th.get_text(strip=True) for th in peer.find_all("th")]
        expected = [
            "Company",
            "Technology/Approach",
            "Scale/Market Signal",
            "Subsidy Dependence",
            "Relative Positioning",
        ]
        if len(headers) != 5:
            errors.append(f"Peer table should have 5 columns, found {len(headers)}.")
        else:
            for i, exp in enumerate(expected):
                if headers[i].lower() != exp.lower():
                    errors.append(f"Peer header mismatch at column {i+1}: expected '{exp}'.")

    # ---------- 7) Compliance checklist ----------
    comp = None
    for h2 in soup.find_all("h2"):
        if "compliance" in h2.get_text().lower():
            comp = h2.find_next(["ul", "ol"])
            break
    if not comp or len(comp.find_all("li")) < 8:
        errors.append("Compliance checklist must have at least 8 items.")

    # ---------- 8) Meta extraction ----------
    match_ticker = re.search(r"\b([A-Z]{2,5})\b", title)
    if match_ticker:
        meta["ticker"] = match_ticker.group(1)
    match_year = re.search(r"([0-9]{1,2})y", body_text)
    if match_year:
        meta["years"] = int(match_year.group(1))

    ok = len(errors) == 0
    return ok, errors, meta
