import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_REPORTS = BASE_DIR / "static_reports"   # folder for your sample HTML files


def generate_spotlight(ticker, projection_years, user_id, email_opt_in):
    """
    Instead of generating real AI report, load the static HTML template
    from /api/static_reports/
    """

    clean = ticker.upper().strip()
    filename = f"DLENS_Spotlight_{clean}.html"
    file_path = STATIC_REPORTS / filename

    if not file_path.exists():
        # return a simple HTML fallback file
        return "/api/reports/not_found.html"

    # return URL where browser can open it
    return f"/api/reports/{filename}"
