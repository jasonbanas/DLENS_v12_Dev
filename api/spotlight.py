import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

# ----------------------------------------------------
# PATHS
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------
# OPENAI CLIENT (RENDER SAFE)
# ----------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ----------------------------------------------------
# CLEAN GPT HTML
# ----------------------------------------------------
def clean_html(text: str):
    """Removes GPT codeblock wrappers (```html, ```)"""
    if not text:
        return ""
    text = text.replace("```html", "")
    text = text.replace("```HTML", "")
    text = text.replace("```", "")
    return text.strip()


# ----------------------------------------------------
# FETCH REAL STOCK PRICE
# ----------------------------------------------------
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

    except:
        return None, None, None, None


# ----------------------------------------------------
# GENERATE FULL V12 SPOTLIGHT HTML FILE
# ----------------------------------------------------
def generate_spotlight(ticker: str, horizon: int):

    ticker = ticker.upper().strip()

    # Fetch live price
    price, change, percent, updated = get_live_price(ticker)
    trend_color = "#16a34a" if (change or 0) >= 0 else "#dc2626"
    sign = "+" if (change or 0) >= 0 else "-"

    # If no price available, display fallback
    if price:
        price_html = f"""
        <div class="price-box">
            <h2>{ticker} — ${price}</h2>
            <p style="color:{trend_color}; font-size:18px;">
                {sign}{abs(change)} ({sign}{abs(percent)}%)
            </p>
            <p class="price-updated">Updated: {updated}</p>
        </div>
        """
    else:
        price_html = f"""
        <div class="price-box">
            <h2>{ticker}</h2>
            <p style="color:#999;">Live price unavailable</p>
        </div>
        """

    # ------------------------------------------------
    # GPT PROMPT — STRICT HTML OUTPUT
    # ------------------------------------------------
    prompt = f"""
    Create a full DLENS v12 GOLD Spotlight report for ticker {ticker}.

    RULES:
    - Output PURE HTML ONLY.
    - NO markdown.
    - NO ```html or ``` code fences.
    - Format must follow professional investment-report style.
    - Must match v12 GOLD layout, white theme, clean sections.
    - Use <h2>, <p>, <ul>, <li>, <table>, <tr>, <td>, <th> only.
    - DO NOT include <html> <head> <body>. I will wrap them.

    Sections required:
    1. Company Summary
    2. DUU & DDI Summary
    3. Why Now
    4. Feasibility vs Dependency (XDLens)
    5. FEP & FVU
    6. Peer Comparison Table
    7. Truth Audit
    8. KPIs
    9. Milestones
    10. Risks
    11. What Would Change The View
    12. Final Investment Take

    Keep output clean, factual, structured.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    gpt_html = clean_html(response.choices[0].message.content)

    # ------------------------------------------------
    # FINAL WRAPPER (WHITE THEME – v12 GOLD)
    # ------------------------------------------------
    final_html = f"""
<!DOCTYPE html>
<html>
<head>
<title>DLENS Spotlight – {ticker}</title>

<style>
body {{
    background:#ffffff;
    color:#0f172a;
    font-family: system-ui, Arial;
    padding: 30px;
}}
h1 {{
    color:#0b5cab;
    text-align:left;
    margin-bottom:5px;
}}
h2 {{
    color:#0b5cab;
    margin-top:32px;
}}
.price-box {{
    background:#f8fafc;
    padding:20px;
    border-radius:12px;
    border:1px solid #e2e8f0;
    margin-bottom:25px;
}}
.price-updated {{
    color:#475569;
    font-size:12px;
}}
.chart-box {{
    margin-top:15px;
    margin-bottom:25px;
}}
table {{
    width:100%;
    border-collapse:collapse;
}}
table, th, td {{
    border:1px solid #e2e8f0;
}}
th {{
    background:#f1f5f9;
    text-align:left;
}}
td, th {{
    padding:10px;
}}
</style>

</head>
<body>

<h1>DLENS Spotlight Report – {ticker}</h1>

{price_html}

<div class="chart-box">
    <iframe src="https://s.tradingview.com/widgetembed/?symbol={ticker}&interval=60&theme=light&style=1"
        width="100%" height="420" frameborder="0">
    </iframe>
</div>

{gpt_html}

</body>
</html>
"""

    # ------------------------------------------------
    # SAVE FILE
    # ------------------------------------------------
    filename = f"DLENS_Spotlight_{ticker}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    return f"/api/reports/{filename}"
