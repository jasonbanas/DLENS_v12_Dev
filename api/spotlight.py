import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI()


# ---------------------------------------------
# Remove GPT Markdown Code Blocks (```html)
# ---------------------------------------------
def clean_gpt_html(text):
    if text is None:
        return ""

    # Remove ```html or ``` at start
    if text.startswith("```html"):
        text = text[len("```html"):]

    if text.startswith("```"):
        text = text[len("```"):]

    # Remove ending ```
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()



# ---------------------------------------------
# Fetch Real-Time Price (Yahoo Finance)
# ---------------------------------------------
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None, None, None, None

        last_price = round(float(data["Close"].iloc[-1]), 2)
        prev_close = round(float(data["Close"].iloc[0]), 2)

        change = round(last_price - prev_close, 2)
        percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        return last_price, change, percent, timestamp

    except Exception:
        return None, None, None, None



# ---------------------------------------------
# Generate Spotlight HTML Report
# ---------------------------------------------
def generate_spotlight(ticker, projection_years, user_id, email_opt_in):

    # Get real-time price
    price, change, percent, timestamp = get_live_price(ticker)

    trend_color = "#22c55e" if (change or 0) >= 0 else "#ef4444"
    sign = "+" if (change or 0) >= 0 else "-"

    price_block = f"""
        <div class="price-box">
            <h2>{ticker.upper()} — ${price}</h2>
            <p style="color:{trend_color}; font-size:18px;">
                {sign}{abs(change)} ({sign}{abs(percent)}%)
            </p>
            <p class="price-updated">Updated: {timestamp}</p>
        </div>
    """ if price else f"""
        <div class="price-box">
            <h2>{ticker.upper()}</h2>
            <p style="color:#aaa;">Live price unavailable</p>
        </div>
    """

    # GPT prompt
    prompt = f"""
    Create a DLENS Spotlight report for ticker: {ticker}.
    VERY IMPORTANT:
    - Output ONLY pure HTML.
    - NEVER use Markdown.
    - NEVER wrap content inside ```html or ``` code blocks.
    - Use ONLY: <h2>, <p>, <table>, <tr>, <th>, <td>, <ul>, <li>

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

    raw_html = response.choices[0].message.content
    gpt_html = clean_gpt_html(raw_html)


    # FINAL HTML OUTPUT
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DLENS Spotlight – {ticker}</title>
        <style>
            body {{
                background: #0d1117;
                color: white;
                font-family: Arial, sans-serif;
                padding: 30px;
            }}
            h1 {{
                color: #58a6ff;
                text-align: center;
            }}
            h2 {{
                color: #58a6ff;
                margin-top: 40px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            table, th, td {{
                border: 1px solid #30363d;
            }}
            td, th {{
                padding: 8px 10px;
            }}
            .price-box {{
                background: #161b22;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
                border: 1px solid #30363d;
            }}
            .chart-box {{
                margin-top: 20px;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>

        <h1>DLENS Spotlight Report — {ticker.upper()}</h1>

        {price_block}

        <div class="chart-box">
            <iframe 
                src="https://s.tradingview.com/widgetembed/?symbol={ticker.upper()}&interval=60&theme=dark&style=1"
                width="100%" height="420" frameborder="0">
            </iframe>
        </div>

        {gpt_html}

    </body>
    </html>
    """

    filename = f"DLENS_Spotlight_{ticker.upper()}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"
