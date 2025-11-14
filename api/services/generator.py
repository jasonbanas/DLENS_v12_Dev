import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_spotlight(ticker, years):
    # TARGET FILE NAME
    filename = f"DLENS_Spotlight_{ticker}.html"
    full_path = os.path.join(REPORTS_DIR, filename)

    # LOOK FOR A PREMADE FILE (e.g. from your TradingView templates)
    template_path = os.path.join(BASE_DIR, "static_reports", f"{ticker.lower()}.html")

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # fallback placeholder
        html = f"""
        <h1>DLENS Spotlight for {ticker}</h1>
        <p>Projection Years: {years}</p>
        <p>Status: Placeholder output.</p>
        """

    # SAVE OUTPUT
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(html)

    return f"/api/reports/{filename}"
