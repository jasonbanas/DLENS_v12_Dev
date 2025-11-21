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
# Remove GPT markdown wrappers
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
# Detect stock exchange (light version)
# ----------------------------
def detect_exchange(ticker):
    """
    Light version using only .info minimal fields.
    """
    try:
        info = yf.Ticker(ticker).fast_info
        exch = info.get("exchange", "")
        if "NASDAQ" in exch.upper(): return "NASDAQ"
        if "NYSE" in exch.upper(): return "NYSE"
        if "AMEX" in exch.upper(): return "AMEX"
        return "NASDAQ"
    except:
        return "NASDAQ"

# ----------------------------
# Light, low-RAM live price fetch
# ----------------------------
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        # VERY LIGHT fetch (no full history)
        price = stock.fast_info.get("last_price", None)
        open_price = stock.fast_info.get("open", None)

        if not price or not open_price:
            return None, None, None, None

        price = round(float(price), 2)
        open_price = round(float(open_price), 2)

        change = round(price - open_price, 2)
        percent = round((change / open_price) * 100, 2)

        timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")

        return price, change, percent, timestamp

    except Exception:
        return None, None, None, None

# ----------------------------
# Generate full v12 Gold Spotlight
# ----------------------------
def generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False):

    ticker = ticker.upper()
    exchange = detect_exchange(ticker)
    symbol_full = f"{exchange}:{ticker}"

    # Price block
    price, change, percent, timestamp = get_live_price(ticker)
    if price is None:
        price_text = "Live price unavailable"
    else:
        sign = "+" if change >= 0 else "-"
        color = "#22c55e" if change >= 0 else "#ef4444"
        price_text = (
            f"${price} (<span style='color:{color}'>"
            f"{sign}{abs(change)} ({sign}{abs(percent)}%)</span>)"
        )

    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    id_short = datetime.now().strftime("%y%m%d")

    # Lighter model for Render Free Tier
    prompt = f"""
Generate a **DLENS Disruptor Spotlight – v12 Gold** report for ticker **{ticker}**.

STRICT REQUIREMENTS:
- OUTPUT **PURE HTML ONLY** — NO markdown or backticks.
- MUST FOLLOW EXACT v12 GOLD STRUCTURE.
- NO <html>, <head>, <body>, NO <style>.
- Return ONLY inner HTML content.

Include required sections 1–17 including:
- DUU
- DDI
- Price Forecast ({horizon}y)
- Peer Table (5 rows)
- A–H Pillars
- Truth Audit
- KPIs
- Milestones
- Risks
- Paradigm Shift
- Compliance Checklist

Return ONLY clean HTML.
"""

    # GPT call – lightweight model
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # <<< LOW RAM MODEL
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(response.choices[0].message.content)

    # Load HTML template
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
# API wrapper (optional params)
# ----------------------------
def generate_spotlight_report(ticker, horizon, user_id=None, email_opt_in=False):
    return generate_spotlight(ticker, horizon, user_id, email_opt_in)
