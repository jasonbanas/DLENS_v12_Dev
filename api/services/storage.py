from pathlib import Path

# Base reports folder (api/reports)
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

# Ensure folder exists
REPORTS_DIR.mkdir(exist_ok=True)


def save_report(user_id: str, ticker: str, html: str):
    """
    Saves a spotlight HTML file into /api/reports/
    Returns: (file_path, url)
    """
    # filename pattern
    filename = f"DLENS_Spotlight_{ticker}.html"

    # full path
    file_path = REPORTS_DIR / filename

    # write HTML file
    file_path.write_text(html, encoding="utf-8")

    # API URL for serving the file
    url = f"/api/reports/{filename}"

    return url, str(file_path)
