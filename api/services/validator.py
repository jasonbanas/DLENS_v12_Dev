import re
from typing import Tuple, List, Dict

RE_DUU = re.compile(r"DUU:?.{5,}", re.I)  # tighten to your exact DUU format
RE_TV_WIDGET = re.compile(r"new\s+TradingView\.widget\s*\(", re.I)
RE_TV_SCRIPT = re.compile(r"<script[^>]*tradingview", re.I)
RE_CSP_BLOCK = re.compile(r"CSP\s*Sources?.*?(Google\s*Finance).*?(Yahoo\s*Finance).*?UTC", re.I | re.S)
RE_PEER_5COL = re.compile(r"<table[^>]*>.*?<tr[^>]*>.*?(<th[^>]*>.*?</th>){5}", re.I | re.S)
RE_TRUTH_AUDIT_3LINE = re.compile(r"Truth\s*Audit.*?(?:\r?\n|\r).*?(?:\r?\n|\r).*?(?:\r?\n|\r)", re.I | re.S)
RE_COMPLIANCE_GTE8 = re.compile(r"Compliance\s*Checklist.*?(<li[^>]*>.*?</li>){8,}", re.I | re.S)
RE_SECTIONS_ORDER = [
    re.compile(r"<h1[^>]*>.*?Overview.*?</h1>", re.I),
    re.compile(r"Peer\s*Table", re.I),
    re.compile(r"Truth\s*Audit", re.I),
    re.compile(r"Compliance\s*Checklist", re.I),
    re.compile(r"CSP\s*Sources?", re.I),
    re.compile(r"TradingView", re.I),
]

def _order_ok(html: str) -> bool:
    pos = 0
    for pat in RE_SECTIONS_ORDER:
        m = pat.search(html, pos)
        if not m:
            return False
        pos = m.end()
    return True

def validate(html: str) -> Tuple[bool, List[str], Dict]:
    errs: List[str] = []
    L = html.lower()
    if "<html" not in L or "<body" not in L: errs.append("Not full HTML.")
    if not RE_DUU.search(html): errs.append("DUU line missing/malformed.")
    if not RE_PEER_5COL.search(html): errs.append("Peer table must have 5 columns.")
    if not RE_TRUTH_AUDIT_3LINE.search(html): errs.append("Truth Audit must have ≥3 lines.")
    if not RE_COMPLIANCE_GTE8.search(html): errs.append("Compliance checklist must have ≥8 items.")
    if not RE_CSP_BLOCK.search(html): errs.append("CSP must include Google Finance + Yahoo Finance + UTC chip.")
    if not RE_TV_SCRIPT.search(html) or not RE_TV_WIDGET.search(html): errs.append("TradingView script + widget required.")
    if not _order_ok(html): errs.append("Sections missing or out of Gold order.")
    return (len(errs) == 0), errs, {"gold_v": "v12", "errs": len(errs)}
