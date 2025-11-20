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
    if text is None:
        return ""
    if text.startswith("```html"):
        text = text[len("```html"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
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
        percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        return last_price, change, percent, timestamp

    except Exception:
        return None, None, None, None


def generate_spotlight(ticker, projection_years, user_id, email_opt_in):

    price, change, percent, timestamp = get_live_price(ticker)

    price_block = f"""
        <div class="price-box">
            <h2>{ticker.upper()} — ${price}</h2>
            <p style="color:#0b5cab; font-size:18px;">
                {change:+} ({percent:+}%)
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
    Create a DLENS v12 GOLD Spotlight Report in pure HTML.
    ⚠️ VERY IMPORTANT:
    - NO Markdown
    - NO ```html blocks
    - Only pure HTML content
    - Keep styling minimal because wrapper template adds the theme

    Sections required:
    1) Short Summary
    2) DUU + DDI
    3) Company Summary
    4) Why Now?
    5) Feasibility (XDLens)
    6) FEP & FVU
    7) Peer Comparison Table
    8) Truth Audit
    9) KPIs
    10) Milestones
    11) Risks
    12) What Changes the View
    13) Conclusion
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_gpt_html(completion.choices[0].message.content)

    # FINAL WRAPPER HTML
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DLENS Spotlight — {ticker}</title>
        <style>
            body {{
                background: #ffffff;
                color: #0f172a;
                font-family: Arial, sans-serif;
                padding: 30px;
            }}
            h1 {{
                color: #0b5cab;
                font-size: 32px;
                text-align: left;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #0b5cab;
            }}
            .price-box {{
                background: #f1f5f9;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
                text-align: center;
                margin-bottom: 20px;
            }}
            iframe {{
                border: none;
            }}
        </style>
    </head>
    <body>

    <h1>DLENS Disruptor Spotlight — v12 Gold</h1>

    {price_block}

    <div>
        <iframe 
            src="https://s.tradingview.com/widgetembed/?symbol={ticker.upper()}&interval=D&theme=light&style=3&withdateranges=1"
            width="100%" height="420">
        </iframe>
    </div>

    {gpt_html}

    </body>
    </html>
    """

    filename = f"DLENS_Spotlight_{ticker.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"
