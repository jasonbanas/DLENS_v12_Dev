import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "spotlight_template.html"

# SAVE REPORTS INSIDE api/static_reports (same place Flask will serve)
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI()


def clean_gpt_html(text):
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```html"):
        t = t[7:]
    if t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def detect_exchange(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        exch = info.get("exchange", "") or ""
        u = exch.upper()
        if "NASDAQ" in u: return "NASDAQ"
        if "NYSE" in u: return "NYSE"
        if "AMEX" in u: return "AMEX"
        return "NASDAQ"
    except:
        return "NASDAQ"


def get_live_price(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.get("last_price")
        open_price = info.get("open")
        if not price or not open_price:
            return None, None, None, None
        price = round(float(price), 2)
        open_price = round(float(open_price), 2)
        change = round(price - open_price, 2)
        pct = round((change / open_price) * 100, 2)
        ts = datetime.now().strftime("%b %d, %Y %I:%M %p")
        return price, change, pct, ts
    except:
        return None, None, None, None


def generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False):

    ticker = ticker.upper()
    exch = detect_exchange(ticker)
    symbol_full = f"{exch}:{ticker}"

    price, chg, pct, ts = get_live_price(ticker)
    if price is None:
        price_block = "Live price unavailable"
    else:
        color = "#22c55e" if chg >= 0 else "#ef4444"
        sign = "+" if chg >= 0 else "-"
        price_block = f"${price} (<span style='color:{color}'>{sign}{abs(chg)} ({sign}{abs(pct)}%)</span>)"

    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    id_short = datetime.now().strftime("%y%m%d")

    prompt = f"""
Generate a DLENS Spotlight v12 Gold report for {ticker}.
Pure HTML only — no markdown, no <html>, no <head>.
Sections 1–17 required.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(resp.choices[0].message.content)

    template = TEMPLATE_PATH.read_text("utf-8")

    final_html = (
        template
        .replace("{{TICKER}}", ticker)
        .replace("{{SYMBOL_FULL}}", symbol_full)
        .replace("{{DATE}}", date_str)
        .replace("{{HORIZON}}", str(horizon))
        .replace("{{PRICE_BLOCK}}", price_block)
        .replace("{{CONTENT}}", gpt_html)
        .replace("{{REPORT_ID}}", f"DLENS_{ticker}_{id_short}_v12_Gold.html")
    )

    filename = f"DLENS_{ticker}_{id_short}_v12_Gold.html"
    filepath = REPORT_DIR / filename

    filepath.write_text(final_html, encoding="utf-8")

    return f"/api/reports/{filename}"


def generate_spotlight_report(ticker, horizon, user_id=None, email_opt_in=False):
    return generate_spotlight(ticker, horizon, user_id, email_opt_in)
