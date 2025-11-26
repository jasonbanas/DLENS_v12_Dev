# api/spotlight.py

import os
from pathlib import Path
from datetime import datetime
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

TEMPLATE_PATH = BASE_DIR / "spotlight_template.html"


def detect_exchange(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        exch = info.get("exchange", "")
        if not exch:
            return "NASDAQ"
        e = exch.upper()
        if "NASDAQ" in e: return "NASDAQ"
        if "NYSE" in e: return "NYSE"
        if "AMEX" in e: return "AMEX"
        return "NASDAQ"
    except:
        return "NASDAQ"


def get_live_price(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.get("last_price")
        open_price = info.get("open")

        if not price or not open_price:
            return None

        price = round(float(price), 2)
        open_price = round(float(open_price), 2)
        change = round(price - open_price, 2)
        percent = round((change / open_price) * 100, 2)

        color = "#22c55e" if change >= 0 else "#ef4444"
        sign = "+" if change >= 0 else "-"

        return f"${price} (<span style='color:{color}'>{sign}{abs(change)} ({sign}{abs(percent)}%)</span>)"
    except:
        return None


def save_spotlight_report(ticker, horizon, html_content):
    ticker = ticker.upper()
    exchange = detect_exchange(ticker)
    symbol_full = f"{exchange}:{ticker}"

    price_block = get_live_price(ticker) or "Live price unavailable"

    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    report_id = f"DLENS_{ticker}_{datetime.now().strftime('%y%m%d')}_v12_Gold.html"

    template = TEMPLATE_PATH.read_text("utf-8")

    final_html = (
        template
        .replace("{{TICKER}}", ticker)
        .replace("{{SYMBOL_FULL}}", symbol_full)
        .replace("{{HORIZON}}", str(horizon))
        .replace("{{DATE}}", date_str)
        .replace("{{PRICE_BLOCK}}", price_block)
        .replace("{{CONTENT}}", html_content)
        .replace("{{REPORT_ID}}", report_id)
    )

    filepath = REPORT_DIR / report_id
    filepath.write_text(final_html, encoding="utf-8")

    return f"/api/reports/{report_id}"
