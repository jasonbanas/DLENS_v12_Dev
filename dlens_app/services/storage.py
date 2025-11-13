# api/services/storage.py
"""
DLENS Storage Service — local persistent save for reports.
"""

import os
from pathlib import Path
from datetime import datetime

# Go two levels up (api → project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

def save_report(user_id: str, ticker: str, html: str):
    """
    Save a DLENS Spotlight report (v12 Gold) to disk.
    Returns (absolute_path, public_url)
    """
    user_folder = REPORTS_DIR / user_id
    user_folder.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%y%m%d")
    file_name = f"DLENS_Spotlight_{ticker.upper()}_ID_{date_str}_GoldStandard_v12.html"
    file_path = user_folder / file_name

    file_path.write_text(html, encoding="utf-8")
    rel_url = f"/reports/{user_id}/{file_name}"
    return str(file_path), rel_url
