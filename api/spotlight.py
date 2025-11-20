import yfinance as yf
from datetime import datetime
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------
# Clean GPT output (remove ```html code blocks)
# ---------------------------------------------
def clean_gpt_html(text):
    if text is None:
        return ""
    text = text.replace("```html", "")
    text = text.replace("```", "")
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
# Generate Spotlight HTML (no file saving)
# ---------------------------------------------
def generate_spotlight(ticker, projection_years, user_id="", email_opt_in=False):

    ticker = ticker.upper()

    # --- Get Live Price ---
    price, change, percent, timestamp = get_live_price(ticker)

    if price:
        trend_color = "#22c55e" if change >= 0 else "#ef4444"
        sign = "+" if change >= 0 else "-"
        price_block = f"""
            <div class="price-box">
                <h2>{ticker} — ${price}</h2>
                <p style="color:{trend_color}; font-size:18px;">
                    {sign}{abs(change)} ({sign}{abs(percent)}%)
                </p>
                <p class="price-updated">Updated: {timestamp}</p>
            </div>
        """
    else:
        price_block = f"""
            <div class="price-box">
                <h2>{ticker}</h2>
                <p style="color:#777;">Live price unavailable</p>
            </div>
        """

    # --- GPT PROMPT ---
    prompt = f"""
    Create a DLENS Spotlight report for ticker {ticker}.
    STRICT REQUIREMENTS:
    - Output pure HTML (NO markdown).
    - Use h2, p, table, tr, th, td, ul, li only.
    - Sections:
        • Company Summary
        • Financial Snapshot (table)
        • DUU Score
        • CSP Anchors
        • {projection_years}-Year Projection Table
        • Highlights
        • Risks
        • Investment Verdict
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(response.choices[0].message.content)

    # --- Final HTML (white v12 layout) ---
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DLENS Spotlight – {ticker}</title>
        <style>
            body {{
                background: #ffffff;
                color: #0f172a;
                font-family: Arial, sans-serif;
                padding: 30px;
                line-height: 1.5;
            }}
            h1 {{
                text-align: center;
                color: #0b5cab;
            }}
            h2 {{
                margin-top: 35px;
                color: #0b5cab;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            th, td {{
                border: 1px solid #e2e8f0;
                padding: 8px;
            }}
            th {{
                background: #f1f5f9;
            }}
            .price-box {{
                background: #f8fafc;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border: 1px solid #e2e8f0;
                margin-bottom: 20px;
            }}
            iframe {{
                border: none;
                border-radius: 12px;
            }}
        </style>
    </head>
    <body>

        <h1>DLENS Spotlight Report — {ticker}</h1>

        {price_block}

        <div class="chart-box">
            <iframe
                src="https://s.tradingview.com/widgetembed/?symbol={ticker}&interval=1D&theme=light&style=1"
                width="100%" height="420">
            </iframe>
        </div>

        {gpt_html}

    </body>
    </html>
    """

    return final_html
