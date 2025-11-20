import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    price, change, percent, timestamp = get_live_price(ticker)

    if price:
        trend_color = "#1a7f37" if change >= 0 else "#d32f2f"
        sign = "+" if change >= 0 else "-"
        price_block = f"""
        <div style="background:#f4f4f4;padding:15px;border-radius:10px;text-align:center;margin-bottom:20px">
            <h2>{ticker} — ${price}</h2>
            <p style="color:{trend_color};font-size:18px;">
                {sign}{abs(change)} ({sign}{abs(percent)}%)
            </p>
            <p>Updated: {timestamp}</p>
        </div>
        """
    else:
        price_block = f"<h3>{ticker}</h3><p>Live price unavailable</p>"

    # GPT content
    prompt = f"""
    Generate a clean HTML DLENS Spotlight report for stock {ticker}.
    Include:
    - Summary
    - DUU Score
    - Risks
    -  {projection_years}-year projection
    Output MUST be PURE HTML ONLY.
    No markdown.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content_html = clean_gpt_html(response.choices[0].message.content)

    final_html = f"""
    <html>
    <head>
        <title>DLENS Spotlight {ticker}</title>
    </head>
    <body style="font-family:Arial;padding:20px;">
        {price_block}
        {content_html}
    </body>
    </html>
    """

    filename = f"DLENS_Spotlight_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"
