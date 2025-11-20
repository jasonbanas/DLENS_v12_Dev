import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI()

def clean_gpt_html(text):
    if not text:
        return ""
    text = text.replace("```html", "").replace("```", "")
    return text.strip()

def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None, None, None, None

        last_price = round(float(data["Close"].iloc[-1]), 2)
        prev_close = round(float(data["Close"].iloc[0]), 2)

        change = round(last_price - prev_close, 2)
        percent = round((change / prev_close) * 100, 2)

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        return last_price, change, percent, timestamp

    except:
        return None, None, None, None


def generate_spotlight(ticker, projection_years, user_id, email_opt_in):

    # LIVE PRICE
    price, change, percent, timestamp = get_live_price(ticker)

    trend_color = "#22c55e" if (change or 0) >= 0 else "#ef4444"
    sign = "+" if (change or 0) >= 0 else "-"

    if price:
        price_block = f"""
        <h2>{ticker.upper()} — ${price}</h2>
        <p style="color:{trend_color}; font-size:18px;">
            {sign}{abs(change)} ({sign}{abs(percent)}%)
        </p>
        <p>Updated: {timestamp}</p>
        """
    else:
        price_block = f"<h2>{ticker.upper()}</h2><p>Live price unavailable</p>"

    # LLM PROMPT
    prompt = f"""
    Create a DLENS Spotlight report for ticker: {ticker}.
    Output PURE HTML ONLY — NO MARKDOWN.
    Do NOT wrap in ```html.

    Include:
    - Company Summary
    - Financial Snapshot (table)
    - DUU Score
    - CSP Anchors
    - {projection_years}-Year Projection Table
    - Highlights
    - Risks
    - Investment Verdict
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(response.choices[0].message.content)

    final_html = f"""
    <html>
    <head>
        <title>DLENS Spotlight – {ticker}</title>
    </head>
    <body>
        <h1>DLENS Spotlight Report — {ticker.upper()}</h1>
        {price_block}

        <iframe 
            src="https://s.tradingview.com/widgetembed/?symbol={ticker.upper()}&interval=60&theme=light"
            width="100%" height="420">
        </iframe>

        {gpt_html}
    </body>
    </html>
    """

    filename = f"DLENS_Spotlight_{ticker.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"
