import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI
import time

BASE_DIR = Path(__file__).resolve().parent

# Report directory
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

TEMPLATE_PATH = BASE_DIR / "spotlight_template.html"

client = OpenAI(
    timeout=12  # prevents Render worker timeout
)

# -------------------------------
# CLEAN GPT HTML BLOCK
# -------------------------------

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


# -------------------------------
# GPT GENERATION with Fallback
# -------------------------------

def gpt_generate(prompt):
    MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "o3-mini"
    ]

    for attempt, model in enumerate(MODELS, start=1):
        try:
            print(f"GPT Attempt {attempt}: {model}")
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=12  # override-level timeout
            )
            text = resp.choices[0].message.content
            return clean_gpt_html(text)

        except Exception as e:
            print(f"[GPT FAIL] {model}: {e}")
            time.sleep(0.5)

    # FINAL FAIL — return safe stub HTML so system NEVER breaks
    return "<div style='padding:20px;color:red;'>GPT generation failed. Please try again.</div>"


# -------------------------------
# YFINANCE HELPERS
# -------------------------------

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
            return None, None, None, None

        price = round(float(price), 2)
        open_price = round(float(open_price), 2)
        change = round(price - open_price, 2)
        percent = round((change / open_price) * 100, 2)
        timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")

        return price, change, percent, timestamp
    except:
        return None, None, None, None


# -------------------------------
# MAIN GENERATOR
# -------------------------------

def generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False):

    ticker = ticker.upper()
    exchange = detect_exchange(ticker)
    symbol_full = f"{exchange}:{ticker}"

    price, change, percent, timestamp = get_live_price(ticker)

    if price is None:
        price_block = "Live price unavailable"
    else:
        sign = "+" if change >= 0 else "-"
        color = "#22c55e" if change >= 0 else "#ef4444"
        price_block = f"${price} (<span style='color:{color}'>{sign}{abs(change)} ({sign}{abs(percent)}%)</span>)"

    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    id_short = datetime.now().strftime("%y%m%d")

    # -----------------------------
    # GPT PROMPT
    # -----------------------------
    prompt = f"""
Generate a DLENS Spotlight v12 Gold HTML report for **{ticker}**.

RULES (MUST FOLLOW):
- Output PURE HTML only (no <html>, <head>, <body>, <style>).
- Follow sections 1–17 exactly.
- Include DUU, DDI, KPIs, Pillars, Risks, Truth Audit.
- Include {horizon}-year forecast.
"""

    # -----------------------------
    # GPT CALL (with Fallback)
    # -----------------------------
    content_html = gpt_generate(prompt)

    # -----------------------------
    # MERGE TEMPLATE
    # -----------------------------
    template = TEMPLATE_PATH.read_text("utf-8")

    final = (
        template
        .replace("{{TICKER}}", ticker)
        .replace("{{SYMBOL_FULL}}", symbol_full)
        .replace("{{DATE}}", date_str)
        .replace("{{HORIZON}}", str(horizon))
        .replace("{{PRICE_BLOCK}}", price_block)
        .replace("{{CONTENT}}", content_html)
        .replace("{{REPORT_ID}}", f"DLENS_{ticker}_{id_short}_v12_Gold.html")
    )

    filename = f"DLENS_{ticker}_{id_short}_v12_Gold.html"
    file_path = REPORT_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final)

    return f"/api/reports/{filename}"


def generate_spotlight_report(ticker, horizon, user_id=None, email_opt_in=False):
    return generate_spotlight(ticker, horizon, user_id, email_opt_in)
