import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "static_reports"
REPORT_DIR.mkdir(exist_ok=True)

client = OpenAI()

# -----------------------------
# Fetch Real Price
# -----------------------------
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
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        return last_price, change, percent, timestamp
    except:
        return None, None, None, None


# -----------------------------
# Generate Spotlight
# -----------------------------
def generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False):

    # Get live price
    price, change, percent, timestamp = get_live_price(ticker)
    tv_symbol = ticker.upper()

    # Ask GPT for structured content
    prompt = f"""
You are DLENS v12 Spotlight engine.
Return ONLY valid JSON with the following fields:

{{
  "company": "",
  "summary": "",
  "duu_expanded": "",
  "duu_score": "",
  "duu_price": "",
  "csp_multiple": "",
  "csp": "",
  "upside": "",
  "duu_probability": "",
  "ddi_label": "",
  "ddi_vectors": "",
  "what_is": "",
  "why_now": ["", "", ""],
  "xd_e": "",
  "xd_s": "",
  "xd_dep": "",
  "xd_mix": "",
  "xd_break": "",
  "fep": "",
  "fvu": "",
  "frogfree": "",
  "peer_table": "<table>...</table>",
  "truth_summary": "",
  "truth_items": ["","",""],
  "kpis": ["","",""],
  "milestones": ["","",""],
  "risks": ["","",""],
  "change_view": ["","",""],
  "conclusion": "",
  "paradigm": "",
  "ddi_details": "",
  "pillars": "",
  "checklist": ["","",""]
}}

Content must be realistic and consistent with DLENS v12 Gold.
Ticker: {ticker}
Horizon: {horizon}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    payload = json.loads(response.choices[0].message.content)

    # -----------------------------
    # Replace into template
    # -----------------------------

    html_template = (BASE_DIR / "templates" / "spotlight.html").read_text(encoding="utf-8")

    final = html_template \
        .replace("{{ company }}", payload["company"]) \
        .replace("{{ ticker }}", ticker.upper()) \
        .replace("{{ horizon }}", str(horizon)) \
        .replace("{{ date }}", timestamp or "") \
        .replace("{{ standard_id }}", f"STD-{ticker.upper()}") \
        .replace("{{ report_id }}", f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M')}") \
        .replace("{{ summary }}", payload["summary"]) \
        .replace("{{ duu_expanded }}", payload["duu_expanded"]) \
        .replace("{{ duu_score }}", payload["duu_score"]) \
        .replace("{{ duu_price }}", payload["duu_price"]) \
        .replace("{{ csp_multiple }}", payload["csp_multiple"]) \
        .replace("{{ csp }}", payload["csp"]) \
        .replace("{{ upside }}", payload["upside"]) \
        .replace("{{ duu_probability }}", payload["duu_probability"]) \
        .replace("{{ ddi_label }}", payload["ddi_label"]) \
        .replace("{{ ddi_vectors }}", payload["ddi_vectors"]) \
        .replace("{{ what_is }}", payload["what_is"]) \
        .replace("{{ xd_e }}", payload["xd_e"]) \
        .replace("{{ xd_s }}", payload["xd_s"]) \
        .replace("{{ xd_dep }}", payload["xd_dep"]) \
        .replace("{{ xd_mix }}", payload["xd_mix"]) \
        .replace("{{ xd_break }}", payload["xd_break"]) \
        .replace("{{ fep }}", payload["fep"]) \
        .replace("{{ fvu }}", payload["fvu"]) \
        .replace("{{ frogfree }}", payload["frogfree"]) \
        .replace("{{ peer_table }}", payload["peer_table"]) \
        .replace("{{ truth_summary }}", payload["truth_summary"]) \
        .replace("{{ conclusion }}", payload["conclusion"]) \
        .replace("{{ paradigm }}", payload["paradigm"]) \
        .replace("{{ ddi_details }}", payload["ddi_details"]) \
        .replace("{{ pillars }}", payload["pillars"]) \
        .replace("{{ tv_symbol }}", tv_symbol)

    # Handle arrays
    def list_to_html(arr):
        return "".join(f"<li>{x}</li>" for x in arr)

    final = final \
        .replace("{% for item in why_now %}", "") \
        .replace("{% endfor %}", "") \
        .replace("{{ why_now }}", list_to_html(payload["why_now"])) \
        .replace("{{ truth_items }}", list_to_html(payload["truth_items"])) \
        .replace("{{ kpis }}", list_to_html(payload["kpis"])) \
        .replace("{{ milestones }}", list_to_html(payload["milestones"])) \
        .replace("{{ risks }}", list_to_html(payload["risks"])) \
        .replace("{{ change_view }}", list_to_html(payload["change_view"])) \
        .replace("{{ checklist }}", list_to_html(payload["checklist"]))

    # -----------------------------
    # Save report
    # -----------------------------
    filename = f"DLENS_Spotlight_{ticker.upper()}.html"
    filepath = REPORT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final)

    return f"/api/reports/{filename}"
