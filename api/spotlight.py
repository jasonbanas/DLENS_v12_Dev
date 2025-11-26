import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent

# Correct directory for saving reports
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

TEMPLATE_PATH = BASE_DIR / "spotlight_template.html"

client = OpenAI()

# -----------------------------
# CLEAN GPT OUTPUT
# -----------------------------
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


# -----------------------------
# SAFE GPT CALL WITH FALLBACK
# -----------------------------
def gpt_generate(prompt):
    """
    Makes a safe GPT call with:
      - Retry (2 attempts)
      - Fallback HTML if GPT fails
    """

    for attempt in range(2):  # Try twice
        try:
            print(f"GPT Attempt {attempt+1}/2...")

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=5000,
                timeout=20,
                messages=[{"role": "user", "content": prompt}]
            )

            content = resp.choices[0].message.content.strip()

            # Validate output — prevent empty files
            if not content or len(content) < 50:
                raise Exception("GPT returned too little content")

            return clean_gpt_html(content)

        except Exception as e:
            print("GPT Error:", str(e))

    # -----------------------------
    # FALLBACK HTML IF GPT FAILS
    # -----------------------------
    print("⚠ GPT FAILED — USING FALLBACK HTML")

    return """
<h2>⚠ Fallback DLENS Spotlight Report</h2>
<p>The system could not generate a full GPT report due to server or memory limits.</p>

<h3>1) Summary</h3>
<p>Fallback summary generated automatically. GPT output unavailable.</p>

<h3>2) DUU + DDI</h3>
<p>DUU: N/A (fallback)<br>DDI: N/A (fallback)</p>

<h3>3) What is the company?</h3>
<p>Information unavailable due to GPT service timeout.</p>

<h3>4) Why Now?</h3>
<p>Fallback mode activated. No AI-generated insights available.</p>

<h3>5–17) Sections</h3>
<p>Standard sections omitted in fallback mode.</p>

<hr>
<p><strong>This ensures a working report is always created — never blank.</strong></p>
"""


# -----------------------------
# DETECT STOCK EXCHANGE
# -----------------------------
def detect_exchange(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        exch = info.get("exchange", "") or ""
        e = exch.upper()
        if "NASDAQ" in e: return "NASDAQ"
        if "NYSE" in e: return "NYSE"
        if "AMEX" in e: return "AMEX"
        return "NASDAQ"
    except:
        return "NASDAQ"


# -----------------------------
# SAFE PRICE FETCH
# -----------------------------
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


# -----------------------------
# MAIN DLENS REPORT GENERATOR
# -----------------------------
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
        price_block = (
            f"${price} (<span style='color:{color}'>"
            f"{sign}{abs(change)} ({sign}{abs(percent)}%)</span>)"
        )

    date_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    id_short = datetime.now().strftime("%y%m%d")

    # ------------------------------------------------------
    # GPT PROMPT (optimized for Render free tier)
    # ------------------------------------------------------
    prompt = f"""
Generate a DLENS Spotlight v12 Gold HTML report for **{ticker}**.

Rules:
- PURE HTML ONLY.
- DO NOT use <html>, <head>, <body>, or <style>.
- Follow EXACT DLENS v12 sections 1–17.
- Include DUU, DDI, peer table, KPIs, Risks, Truth Audit, A–H Pillars.
- Include a {horizon}-year forecast.
- Keep formatting simple & valid HTML.
"""

    # SAFE GPT WRAPPER
    content_html = gpt_generate(prompt)

    # Load template
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

    # WRITE SAFE HTML FILE
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final)

    return f"/api/reports/{filename}"


def generate_spotlight_report(ticker, horizon, user_id=None, email_opt_in=False):
    return generate_spotlight(ticker, horizon, user_id, email_opt_in)
