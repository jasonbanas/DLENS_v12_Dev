# ============================================
# spotlight.py (Business Logic for Spotlight)
# ============================================

from pathlib import Path
import uuid
import datetime
import json


# Location of generated reports
BASE_DIR = Path(__file__).resolve().parent
STATIC_REPORTS = BASE_DIR / "static_reports"
STATIC_REPORTS.mkdir(exist_ok=True)


def generate_spotlight(ticker: str, projection_years: int = 10, user_id="demo", email_opt_in=False):
    """
    Main business logic used by the Vercel Serverless Function.
    This version is a CLEAN template — insert your real logic here.

    Args:
        ticker (str): Stock ticker symbol.
        projection_years (int): Number of years to project.
        user_id (str): Optional user ID or email.
        email_opt_in (bool): Whether user opted into email updates.

    Returns:
        str: Public URL to the generated report.
    """

    # ---------------------------------------------------------------------
    # 1. Validate Inputs
    # ---------------------------------------------------------------------
    ticker = ticker.upper().strip()

    if not ticker:
        raise ValueError("Ticker cannot be empty")

    # Make filename
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    file_id = f"{ticker}-{timestamp}-{uuid.uuid4().hex[:8]}.html"

    output_file = STATIC_REPORTS / file_id

    # ---------------------------------------------------------------------
    # 2. INSERT YOUR REAL REPORT-GENERATION LOGIC HERE
    # ---------------------------------------------------------------------
    #
    # Example placeholder content:
    html = f"""
    <html>
    <head><title>Spotlight Report - {ticker}</title></head>
    <body>
        <h1>Spotlight Report</h1>
        <p><strong>Ticker:</strong> {ticker}</p>
        <p><strong>Projection Years:</strong> {projection_years}</p>
        <p><strong>User:</strong> {user_id}</p>
        <p><strong>Email Opt-in:</strong> {email_opt_in}</p>

        <h2>Sample Output</h2>
        <p>This is a placeholder Spotlight report.</p>
        <p>Replace this with your actual financial model.</p>
    </body>
    </html>
    """

    # Write report to file
    output_file.write_text(html, encoding="utf-8")

    # ---------------------------------------------------------------------
    # 3. Return Vercel Public URL
    # ---------------------------------------------------------------------
    public_url = f"/api/reports/{file_id}"

    return public_url


# For local debug (Optional)
if __name__ == "__main__":
    url = generate_spotlight("AAPL", 10)
    print("Generated:", url)
