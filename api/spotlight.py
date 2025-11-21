import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI()

# ----------------------------
# Remove GPT markdown
# ----------------------------
def clean_gpt_html(text):
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```html"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# ----------------------------
# Get real stock exchange
# ----------------------------
def detect_exchange(ticker):
    try:
        info = yf.Ticker(ticker).info
        exch = info.get("exchange", "")
        if not exch:
            return "NASDAQ"

        if "Nasdaq" in exch or "NASDAQ" in exch:
            return "NASDAQ"
        if "NYSE" in exch:
            return "NYSE"
        if "AMEX" in exch:
            return "AMEX"
        return "NASDAQ"
    except:
        return "NASDAQ"

# ----------------------------
# Live price
# ----------------------------
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None, None, None, None

        last_price = round(float(data["Close"].iloc[-1]), 2)
        first_price = round(float(data["Open"].iloc[0]), 2)

        change = round(last_price - first_price, 2)
        percent = round((change / first_price) * 100, 2)

        timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")

        return last_price, change, percent, timestamp

    except Exception:
        return None, None, None, None

# ----------------------------
# Generate full v12 Gold Spotlight
# ----------------------------
def generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False):

    ticker = ticker.upper()
    exchange = detect_exchange(ticker)
    symbol_full = f"{exchange}:{ticker}"

    # Price
    price, change, percent, timestamp = get_live_price(ticker)
    if price is None:
        price_text = "Live price unavailable"
    else:
        sign = "+" if change >= 0 else "-"
        price_text = (
            f"${price}  (<span style='color:{'#22c55e' if change>=0 else '#ef4444'}'>"
            f"{sign}{abs(change)} ({sign}{abs(percent)}%)</span>)"
        )

    # Date (v12 style)
    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")

    # ID
    id_short = datetime.now().strftime("%y%m%d")

    # GPT Prompt
    prompt = f"""
Generate a **DLENS Disruptor Spotlight – v12 Gold** report for ticker **{ticker}**.

STRICT REQUIREMENTS:
- OUTPUT **PURE HTML ONLY** — NO markdown, NO backticks.
- MUST FOLLOW EXACT v12 GOLD STRUCTURE & STYLE.
- MUST RETURN ONLY the inside sections (no <html>, no <head>, no <body>).
- DO NOT include <style>. Only HTML content.
- MUST USE SECTIONS EXACTLY:
  1) Short Summary
  2) DUU + DDI
  3) What is the company?
  4) Why now?
  5) Feasibility vs Dependency (XDLens)
  6) FEP & FVU
  7) Peer Comparison — STRICT TABLE
  8) Truth Audit — HARD FORMAT
  9) KPIs
  10) Milestones
  11) Risks
  12) What would change the view?
  13) Decision-Ready Conclusion
  14) Paradigm Shift
  15) DDI Details
  16) Appendix — A–H Pillars
  17) Compliance Checklist (v12)

Include:
- DUU Score
- Most-Likely Price ({horizon}y)
- CSP (two-source)
- Chips section
- Pillars A–H table
- Peer comparison strict table (5 rows)
- TSLA/JOBY structure

Return ONLY clean HTML.
"""

    # GPT Call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(response.choices[0].message.content)

    # Load template
    template_path = BASE_DIR / "spotlight_template.html"
    template = template_path.read_text(encoding="utf-8")

    final_html = (
        template
        .replace("{{TICKER}}", ticker)
        .replace("{{SYMBOL_FULL}}", symbol_full)
        .replace("{{DATE}}", date_str)
        .replace("{{HORIZON}}", str(horizon))
        .replace("{{PRICE_BLOCK}}", price_text)
        .replace("{{REPORT_ID}}", f"DLENS_Spotlight_{ticker}_ID_{id_short}_v12_Gold.html")
        .replace("{{CONTENT}}", gpt_html)
    )

    filename = f"DLENS_Spotlight_{ticker}_ID_{id_short}_v12_Gold.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"

# ----------------------------
# WRAPPER FOR API IMPORT (OPTIONAL ARGS)
# ----------------------------
def generate_spotlight_report(ticker, horizon, user_id=None, email_opt_in=False):
    """
    Wrapper used by /api/spotlight.
    Makes user_id + email_opt_in optional so frontend calls work.
    """
    return generate_spotlight(ticker, horizon, user_id, email_opt_in)
